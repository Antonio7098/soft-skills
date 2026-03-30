"""Voice transcription WebSocket endpoint."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from soft_skills_backend.entrypoints.http.dependencies import get_actor_from_websocket
from soft_skills_backend.modules.voice import TranscriptionError, VoiceTranscriptionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/transcribe-ws")
async def transcribe_websocket(websocket: WebSocket):
    """WebSocket endpoint for streaming voice transcription.

    Protocol:
        1. Client sends audio chunks as binary messages
        2. Server sends transcripts as JSON text messages:
            {"text": "...", "is_final": bool, "speech_final": bool}
        3. Server sends errors as JSON:
            {"error": "...", "code": "..."}
        4. Client sends {"type": "stop"} to end session
        5. Server sends {"type": "close"} when done
    """
    await websocket.accept()

    actor = await get_actor_from_websocket(websocket)
    if not actor:
        await websocket.send_json({"error": "Unauthorized", "code": "AUTH_001"})
        await websocket.close()
        return

    audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    transcript_queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    async def run_transcription() -> None:
        """Run the transcription service."""
        try:
            service = VoiceTranscriptionService()
            await service.transcribe_stream(audio_queue, transcript_queue)
        except TranscriptionError as e:
            await transcript_queue.put({"error": e.message, "code": e.code})
        except Exception as e:
            logger.exception("Unexpected transcription error")
            await transcript_queue.put({"error": str(e), "code": "UNKNOWN"})
        finally:
            await transcript_queue.put(None)

    async def transcript_sender() -> None:
        """Send transcripts back to client."""
        try:
            while True:
                result = await transcript_queue.get()
                if result is None:
                    await websocket.send_json({"type": "close"})
                    break
                if "error" in result:
                    await websocket.send_json(result)
                    break
                await websocket.send_json(result)
        except WebSocketDisconnect:
            pass
        except Exception:
            logger.exception("Error sending transcript")

    transcription_task = asyncio.create_task(run_transcription())
    sender_task = asyncio.create_task(transcript_sender())

    try:
        while True:
            data = await websocket.receive()

            if data["type"] == "websocket.disconnect":
                break

            if data["type"] == "websocket.receive":
                if "text" in data:
                    try:
                        msg = json.loads(data["text"])
                        if msg.get("type") == "stop":
                            break
                    except json.JSONDecodeError:
                        pass
                elif "bytes" in data:
                    await audio_queue.put(data["bytes"])

    except WebSocketDisconnect:
        pass
    finally:
        await audio_queue.put(None)
        transcription_task.cancel()
        sender_task.cancel()
        with suppress(asyncio.CancelledError):
            await transcription_task
        with suppress(asyncio.CancelledError):
            await sender_task
