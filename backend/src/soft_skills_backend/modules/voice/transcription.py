"""Voice transcription service using Deepgram."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from soft_skills_backend.config import get_settings

try:
    from deepgram import DeepgramClient
    from deepgram.contracts import TranscriptionControl

    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False
    DeepgramClient = None
    TranscriptionControl = None

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Raised when transcription fails."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class VoiceTranscriptionService:
    """Service for streaming voice transcription via Deepgram."""

    def __init__(self) -> None:
        if not DEEPGRAM_AVAILABLE:
            raise TranscriptionError(
                "Deepgram SDK not installed. Run: pip install deepgram-sdk",
                code="VOICE_000",
            )
        settings = get_settings()
        api_key = settings.deepgram_api_key
        if not api_key:
            raise TranscriptionError(
                "Deepgram API key not configured",
                code="VOICE_001",
            )
        self._client = DeepgramClient(api_key=api_key)
        self._model = settings.deepgram_model
        self._language = settings.deepgram_language

    async def transcribe_stream(
        self,
        audio_iterator: asyncio.Queue[bytes],
        transcript_callback: asyncio.Queue[dict[str, Any] | None],
    ) -> None:
        """Stream transcription results from audio chunks.

        Args:
            audio_iterator: Queue of raw audio bytes (webm/opus)
            transcript_callback: Queue to receive transcription results as dicts
        """

        try:
            connection = self._client.listen.v1.connect(
                model=self._model,
                language=self._language,
                smart_format=True,
                interim_results=True,
            )

            connection.on(
                TranscriptionControl.Open,
                lambda _: logger.info("Deepgram connection opened"),
            )

            connection.on(
                TranscriptionControl.Close,
                lambda _: logger.info("Deepgram connection closed"),
            )

            connection.on(
                TranscriptionControl.Error,
                lambda e: logger.error(f"Deepgram error: {e}"),
            )

            connection.on(
                TranscriptionControl.TranscriptReceived,
                lambda msg: self._handle_transcript(msg, transcript_callback),
            )

            connection.connect()
            await connection.wait_for_open()

            async def send_audio() -> None:
                while True:
                    try:
                        chunk = await asyncio.wait_for(audio_iterator.get(), timeout=30.0)
                        if chunk is None:
                            break
                        connection.send_media(chunk)
                    except TimeoutError:
                        connection.send_keep_alive()
                    except asyncio.CancelledError:
                        break

            sender = asyncio.create_task(send_audio())

            try:
                await sender
            except asyncio.CancelledError:
                sender.cancel()
                await audio_iterator.put(None)

        except Exception as e:
            logger.exception("Transcription stream failed")
            transcript_callback.put_nowait({"error": str(e), "code": "VOICE_STREAM_ERROR"})

    def _handle_transcript(
        self,
        msg: object,
        callback: asyncio.Queue[dict[str, Any] | None],
    ) -> None:
        """Handle incoming transcript from Deepgram."""
        try:
            msg_dict = msg.to_dict() if hasattr(msg, "to_dict") else msg
            if not isinstance(msg_dict, dict):
                return

            if msg_dict.get("type") == "Results":
                channel = msg_dict.get("channel", {})
                alternatives = channel.get("alternatives", [{}])
                if not alternatives:
                    return

                transcript = alternatives[0].get("transcript", "")
                if not transcript:
                    return

                callback.put_nowait(
                    {
                        "text": transcript,
                        "is_final": msg_dict.get("is_final", False),
                        "speech_final": msg_dict.get("speech_final", False),
                    }
                )

            elif msg_dict.get("type") == "Error":
                error_msg = msg_dict.get("error", "Unknown error")
                callback.put_nowait({"error": error_msg, "code": "DEEPGRAM_ERROR"})

        except Exception as e:
            logger.exception("Failed to handle transcript")
            callback.put_nowait({"error": str(e), "code": "TRANSCRIPT_PARSE_ERROR"})
