/**
 * useVoiceInput hook - hybrid Web Speech API + backend Deepgram proxy.
 *
 * Architecture:
 * - Chrome/Edge: Uses native Web Speech API (continuous, interim results)
 * - On 'network' error from Web Speech API: Falls back to Deepgram WebSocket
 * - Other browsers: Uses WebSocket to backend which streams to Deepgram
 *
 * WebSocket protocol:
 * - Client sends binary audio chunks
 * - Client sends {"type": "stop"} to end
 * - Server sends {"text": "...", "is_final": bool, "speech_final": bool}
 * - Server sends {"error": "...", "code": "..."} on error
 * - Server sends {"type": "close"} when done
 */

import { useCallback, useRef, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

export interface UseVoiceInputOptions {
  onTranscript: (transcript: string, isFinal: boolean) => void;
  language?: string;
}

export interface UseVoiceInputReturn {
  isListening: boolean;
  error: string | null;
  start: () => Promise<void>;
  stop: () => void;
  isSupported: boolean;
  browserSupportsWebSpeech: boolean;
}

function browserSupportsWebSpeech(): boolean {
  if (typeof window === 'undefined') return false;
  return !!(window.SpeechRecognition || (window as typeof window & { webkitSpeechRecognition: typeof SpeechRecognition }).webkitSpeechRecognition);
}

const CHROME_OR_EDGE = typeof navigator !== 'undefined' && /Chrome|Edg/.test(navigator.userAgent);

export function useVoiceInput({ onTranscript, language = 'en-US' }: UseVoiceInputOptions): UseVoiceInputReturn {
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const onTranscriptRef = useRef(onTranscript);
  onTranscriptRef.current = onTranscript;

  const stop = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.onend = null;
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify({ type: 'stop' }));
      websocketRef.current.close();
      websocketRef.current = null;
    }

    setIsListening(false);
  }, []);

  const startDeepgramFallback = useCallback(async (existingStream?: MediaStream) => {
    let stream = existingStream;
    if (!stream) {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    }
    streamRef.current = stream;

    const userId = sessionStorage.getItem('ss_user_id');
    const orgId = sessionStorage.getItem('ss_active_organisation_id');
    const params = new URLSearchParams();
    if (userId) params.set('user_id', userId);
    if (orgId) params.set('organisation_id', orgId);

    const wsUrl = `${API_BASE.replace(/^http/, 'ws')}/voice/transcribe-ws?${params.toString()}`;
    const ws = new WebSocket(wsUrl);
    websocketRef.current = ws;

    const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    mediaRecorderRef.current = mediaRecorder;

    ws.onopen = () => {
      mediaRecorder.start(100);
      setIsListening(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'close') {
          stop();
          return;
        }

        if (data.error) {
          setError(data.error);
          stop();
          return;
        }

        if (data.text) {
          onTranscriptRef.current(data.text, data.is_final);
        }
      } catch {
        // Ignore parse errors
      }
    };

    ws.onerror = () => {
      setError('WebSocket connection error');
      stop();
    };

    ws.onclose = () => {
      if (mediaRecorderRef.current?.state !== 'inactive') {
        mediaRecorderRef.current?.stop();
      }
      setIsListening(false);
    };

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
        ws.send(event.data);
      }
    };

    mediaRecorder.onerror = (event) => {
      setError(`Recording error: ${(event as Error).message || 'Unknown error'}`);
      stop();
    };
  }, [stop]);

  const start = useCallback(async () => {
    setError(null);

    if (browserSupportsWebSpeech() && CHROME_OR_EDGE) {
      const SpeechRecognition = window.SpeechRecognition || (window as typeof window & { webkitSpeechRecognition: typeof SpeechRecognition }).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();

      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = language;

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        if (interimTranscript) {
          onTranscript(interimTranscript, false);
        }
        if (finalTranscript) {
          onTranscript(finalTranscript, true);
        }
      };

      recognition.onerror = async (event: SpeechRecognitionErrorEvent) => {
        if (event.error === 'no-speech') {
          setError(null);
          setIsListening(false);
        } else if (event.error === 'network') {
          // Fall back to Deepgram WebSocket transcription
          recognitionRef.current = null;
          try {
            await startDeepgramFallback();
          } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            if (message.includes('Permission denied') || message.includes('NotAllowedError')) {
              setError('Microphone permission denied. Please allow microphone access.');
            } else if (message.includes('NotFoundError')) {
              setError('No microphone found. Please connect a microphone.');
            } else {
              setError(message);
            }
            setIsListening(false);
          }
        } else {
          setError(event.error);
          setIsListening(false);
        }
      };

      recognition.onend = () => {
        if (isListening && recognitionRef.current === recognition) {
          try {
            recognition.start();
          } catch {
            setIsListening(false);
          }
        }
      };

      try {
        recognition.start();
        recognitionRef.current = recognition;
        setIsListening(true);
      } catch (err) {
        setError('Failed to start speech recognition');
        setIsListening(false);
      }
    } else {
      try {
        await startDeepgramFallback();
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        if (message.includes('Permission denied') || message.includes('NotAllowedError')) {
          setError('Microphone permission denied. Please allow microphone access.');
        } else if (message.includes('NotFoundError')) {
          setError('No microphone found. Please connect a microphone.');
        } else {
          setError(message);
        }
        stop();
      }
    }
  }, [language, onTranscript, stop, isListening, startDeepgramFallback]);

  return {
    isListening,
    error,
    start,
    stop,
    isSupported: true,
    browserSupportsWebSpeech: browserSupportsWebSpeech(),
  };
}
