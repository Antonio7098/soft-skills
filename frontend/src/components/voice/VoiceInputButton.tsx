/**
 * Voice input toggle button with recording indicator.
 */

import { Mic, MicOff, Waves } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { cn } from '@/lib/cn';
import { Button } from '@/design-system/primitives/Button';
import { useVoiceInput } from '@/hooks/useVoiceInput';

interface VoiceInputButtonProps {
  onTranscript: (transcript: string, isFinal: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export function VoiceInputButton({ onTranscript, disabled = false, className }: VoiceInputButtonProps) {
  const [showError, setShowError] = useState<string | null>(null);

  const { isListening, error, start, stop, browserSupportsWebSpeech } = useVoiceInput({
    onTranscript: (text, isFinal) => {
      onTranscript(text, isFinal);
    },
  });

  useEffect(() => {
    if (error) {
      setShowError(error);
      const timer = setTimeout(() => setShowError(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const handleClick = useCallback(async () => {
    if (isListening) {
      stop();
    } else {
      setShowError(null);
      await start();
    }
  }, [isListening, start, stop]);

  const isAvailable = browserSupportsWebSpeech;

  if (!isAvailable) {
    return null;
  }

  return (
    <div className={cn('relative', className)}>
      <Button
        variant={isListening ? 'secondary' : 'ghost'}
        size="sm"
        onClick={handleClick}
        disabled={disabled}
        className={cn(
          'relative transition-all duration-200',
          isListening && 'bg-accent/10 border-accent/30',
        )}
        aria-label={isListening ? 'Stop recording' : 'Start voice input'}
        title={showError || (isListening ? 'Listening...' : 'Voice input')}
      >
        <span className={cn('transition-transform duration-200', isListening && 'scale-110')}>
          {isListening ? (
            <Waves className="w-4 h-4 text-accent animate-pulse" />
          ) : (
            <Mic className="w-4 h-4" />
          )}
        </span>

        {isListening && (
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-accent"></span>
          </span>
        )}
      </Button>

      {showError && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-status-error text-surface-primary text-body-xs rounded-lg whitespace-nowrap z-50 shadow-lg">
          <MicOff className="w-3 h-3 inline mr-1" />
          {showError}
        </div>
      )}
    </div>
  );
}
