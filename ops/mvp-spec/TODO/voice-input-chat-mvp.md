# Voice Input for Chat (Hybrid: Web Speech API + Backend-Proxy Deepgram)

## Context

Users want Gboard-style continuous voice input in the chatbot. Unlike traditional "record then transcribe", it should stream transcription as they speak.

**Constraint**: Must work on all browsers (Chrome, Firefox, Safari, Edge).

## Approach: Hybrid Strategy

| Browser | Primary | Fallback |
|---------|---------|----------|
| Chrome/Edge | Web Speech API (free, built-in) | Backend-proxy Deepgram |
| Firefox/Safari | Backend-proxy Deepgram | - |

Web Speech API (`webkitSpeechRecognition`) provides true real-time transcription in Chromium browsers but is unavailable in Firefox/Safari. Backend-proxy Deepgram works everywhere with proper API key security.

---

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │              Browser                     │
                    │                                          │
ChatInput           │  VoiceInputButton                        │
    │               │       │                                  │
    │               │       ▼                                  │
    │               │  useVoiceInput                           │
    │               │       │                                  │
    │               │   ┌───┴───┐                              │
    │               │   │       │                              │
    │               │   ▼       ▼                              │
    │               │ Web     MediaRecorder ───────────────────┤
    │               │ Speech     │                             │
    │               │ API        ▼                             │
    │               │         ChunkedAudio ────────────────────►│
    │               │                                              │
◄───transcript──────┘◄───SSE transcript stream──────────────────────┤
                    │                                              │
                    └──────────────────────────────────────────────┘
                                             │
                                             ▼ HTTP/SSE
                    ┌──────────────────────────────────────────────┐
                    │              Backend                          │
                    │                                              │
                    │  POST /api/voice/transcribe-stream           │
                    │       │                                      │
                    │       ▼                                      │
                    │  VoiceTranscribeEndpoint                    │
                    │       │                                      │
                    │       ▼                                      │
                    │  DeepgramWebSocket                          │
                    │       │                                      │
                    │       ▼                                      │
                    │  @deepgram/sdk ◄── audio chunks             │
                    │       │                                      │
                    │       ▼                                      │
                    │  Transcript ────────────────────────────────►│ SSE
                    │                                              │
                    └──────────────────────────────────────────────┘
```

**Flow**:
1. Frontend captures audio via `MediaRecorder` (webm/opus)
2. Chunks sent via HTTP POST to `/api/voice/transcribe-stream`
3. Backend proxies chunks to Deepgram WebSocket
4. Backend receives transcripts and streams back via SSE
5. Frontend `useVoiceInput` hook receives transcript callbacks

---

## Implementation Plan

### Phase 1: Backend - Voice Transcription Endpoint

**File**: `backend/src/soft_skills_backend/`

**Route**: `POST /api/voice/transcribe-stream`
- Accepts: `audio/webm` or `audio/opus` chunks in request body
- Returns: `text/event-stream` (SSE) with transcripts
- Uses: `@deepgram/sdk` server-side with API key from env

**New module structure**:
```
backend/src/soft_skills_backend/
├── entrypoints/
│   └── http/
│       └── routers/
│           └── voice.py              # Transcription router
├── modules/
│   └── voice/
│       ├── __init__.py
│       ├── transcription.py           # Deepgram integration
│       └── schemas.py                # Pydantic models
└── platform/
    └── providers/
        └── deepgram.py               # Deepgram client wrapper
```

**Key design**:
- Streaming endpoint using FastAPI `StreamingResponse`
- Audio chunks buffered and sent to Deepgram WebSocket
- Deepgram responses parsed and forwarded as SSE events
- Connection lifecycle managed per-request

**Environment variable**: `DEEPGRAM_API_KEY` in `backend/.env`

### Phase 2: Hook Foundation (Frontend)

**File**: `frontend/src/hooks/useVoiceInput.ts`

Create the `useVoiceInput` hook that:
- Accepts `onTranscript` callback for interim and final results
- Exposes `isListening`, `error`, `start`, `stop`
- Tries Web Speech API first; falls back to `POST /api/voice/transcribe-stream`
- Uses `continuous: true` and `interimResults: true` for Web Speech
- Handles microphone permissions

```typescript
interface UseVoiceInputOptions {
  onTranscript: (transcript: string, isFinal: boolean) => void;
  language?: string;
}

interface UseVoiceInputReturn {
  isListening: boolean;
  error: string | null;
  start: () => Promise<void>;
  stop: () => void;
  isSupported: boolean;
  browserSupportsWebSpeech: boolean;
  transcriptBackend: string | null;  // Backend endpoint
}
```

**Detection logic**:
```typescript
const browserSupportsWebSpeech = !!(
  typeof window !== 'undefined' && 
  (window.SpeechRecognition || window.webkitSpeechRecognition)
);
```

**Backend fallback** (browser doesn't support Web Speech):
```typescript
async function sendAudioChunk(chunk: Blob) {
  const response = await fetch('/api/voice/transcribe-stream', {
    method: 'POST',
    body: chunk,
    headers: { 'Content-Type': 'audio/webm' },
  });
  // Parse SSE stream for transcripts
}
```

### Phase 3: UI Component

**File**: `frontend/src/components/voice/VoiceInputButton.tsx`

A button that:
- Shows microphone icon when idle
- Shows pulsing/recording indicator when active
- Toggles recording on click
- Integrates with `useVoiceInput` hook

Design system compliance:
- Uses existing `Button` primitive from `@/design-system/primitives/Button`
- Uses `lucide-react` icons (`Mic`, `MicOff`, `Waves`)
- Follows token-driven theming

**States**:
- Idle: microphone icon, accent color
- Listening: animated waves, pulsing indicator
- Error: red state with tooltip

### Phase 4: ChatInput Integration

**File**: `frontend/src/features/chat/ChatInput.tsx`

Modify `ChatInput` to:
- Accept new props: `onVoiceTranscript` (optional)
- Render `VoiceInputButton` when `onVoiceTranscript` provided
- When voice transcript arrives (interim or final), append to textarea or send directly

**Props expansion**:
```typescript
interface ChatInputProps {
  // ... existing
  onVoiceTranscript?: (transcript: string, isFinal: boolean) => void;
  voiceInputEnabled?: boolean;
}
```

### Phase 5: Error Handling & Edge Cases

Handle:
- Microphone permission denied → show informative error
- Web Speech API unavailable + backend fails → disable voice button
- Backend API errors → fallback message, retry logic
- Browser tab hidden → pause recording
- Network interruption → reconnect with backoff

---

## File Structure

```
backend/src/soft_skills_backend/
├── entrypoints/http/routers/
│   └── voice.py                      # POST /api/voice/transcribe-stream
├── modules/voice/
│   ├── __init__.py
│   ├── transcription.py               # Deepgram WebSocket logic
│   └── schemas.py                     # Request/response models
└── platform/providers/
    └── deepgram.py                    # Deepgram client wrapper

frontend/src/
├── hooks/
│   └── useVoiceInput.ts               # Main hook
├── components/
│   └── voice/
│       └── VoiceInputButton.tsx       # Toggle button
└── features/chat/
    └── ChatInput.tsx                  # Modified to use voice
```

---

## Dependencies

**Backend**:
```bash
pip install deepgram-sdk
```

**Frontend**:
No new dependencies. Web Speech API is built-in; `fetch` + `EventSource` for SSE.

---

## Environment Variables

```env
# backend/.env
DEEPGRAM_API_KEY=your_deepgram_api_key_here
```

```env
# frontend/.env (optional, for dev)
VITE_API_BASE=http://localhost:8000/api
```

Free Deepgram tier: 200 min/month. Get key at https://console.deepgram.com/

---

## API Contract

### POST /api/voice/transcribe-stream

**Request**:
- Method: `POST`
- Headers: `Content-Type: audio/webm` (or `audio/opus`)
- Body: Raw audio bytes (chunks from MediaRecorder)

**Response**:
- Type: `text/event-stream` (SSE)
- Events:

```
event: transcript
data: {"text": "Hello ", "is_final": false, "speech_final": false}

event: transcript
data: {"text": "Hello world", "is_final": true, "speech_final": true}

event: error
data: {"error": "Deepgram connection failed"}

event: close
data: {}
```

**Notes**:
- `is_final: false` = interim result, may change
- `speech_final: true` = end of speech detected
- Client should accumulate `is_final: true` transcripts

---

## Testing Considerations

1. **Web Speech API**: Test in Chrome, Edge (mic permission, continuous mode, interim results)
2. **Backend proxy**: Test in Firefox/Safari (requires valid API key)
3. **Hybrid switch**: Temporarily disable Web Speech to verify backend kicks in
4. **Error states**: Deny mic permission, invalid API key, network failure
5. **Chunking**: Verify audio chunks are small enough for real-time (< 500ms)

---

## Constitution Alignment

| Rule | Alignment |
|------|-----------|
| CL-004 (SOLID) | Hook and client have single responsibility; clear interface boundaries |
| CL-011 (Reusability) | `useVoiceInput` is reusable; `VoiceInputButton` uses design system primitives |
| CL-012 (Alive) | Recording state shows visual feedback immediately |
| CL-003 (Fail Loud) | Errors surface to UI; no silent fallbacks |
| CL-005 (Observability) | Backend logs all transcription requests |
| CL-013 (API Boundaries) | Explicit request/response contracts via Pydantic and SSE |

---

## Out of Scope (Future)

- Text-to-speech (TTS) for reading responses aloud
- Audio recording and storage for later playback
- Speaker identification
- Multi-language auto-detection
- Voice activity detection (VAD) tuning

---

## Verification

After implementation:
1. Backend: `make lint && make typecheck` passes
2. Frontend: `npx tsc --noEmit` passes
3. Voice button appears in ChatInput
4. Chrome: Web Speech works without API key
5. Firefox/Safari: Backend proxy works with API key
6. Interim results appear as you speak
7. Final transcript populates and can be sent

---

## Implementation Status

### Completed

- [x] Backend: `modules/voice/__init__.py` - module init
- [x] Backend: `modules/voice/schemas.py` - Pydantic models
- [x] Backend: `modules/voice/transcription.py` - Deepgram service (lazy import)
- [x] Backend: `entrypoints/http/routes/voice.py` - WebSocket endpoint (bidirectional)
- [x] Backend: Added deepgram-sdk to pyproject.toml
- [x] Backend: Added DEEPGRAM_API_KEY, deepgram_model, deepgram_language config
- [x] Backend: Added voice router to api_router
- [x] Frontend: `hooks/useVoiceInput.ts` - hybrid hook (Web Speech + WebSocket)
- [x] Frontend: `components/voice/VoiceInputButton.tsx` - mic toggle button
- [x] Frontend: Integrated VoiceInputButton into ChatInput
- [x] Frontend: Interim transcripts shown in real-time (italic, lighter color)

### Architecture: True Continuous Transcription

**WebSocket Protocol** (`/api/voice/transcribe-ws`):
- Frontend sends: raw audio chunks (binary)
- Frontend sends: `{"type": "stop"}` to end
- Backend sends: `{"text": "...", "is_final": bool, "speech_final": bool}` (interim and final)
- Backend sends: `{"type": "close"}` when done

**Flow**:
1. User clicks mic → WebSocket opens
2. MediaRecorder sends 100ms chunks via WebSocket
3. Backend forwards chunks to Deepgram WebSocket
4. Deepgram streams interim results back
5. Backend forwards interim results to frontend
6. Frontend shows interim in italic, final replaces it
7. User clicks stop or sends → mic off, text ready

### Pending

- [ ] Backend: Install dependencies (`pip install deepgram-sdk`)
- [ ] Backend: Add `.env` with `DEEPGRAM_API_KEY`
- [ ] Testing: Manual browser testing in Chrome and Firefox/Safari
