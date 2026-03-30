"""Pydantic schemas for voice transcription."""

from __future__ import annotations

from pydantic import BaseModel


class TranscriptionTranscript(BaseModel):
    """A single transcription result."""

    text: str
    is_final: bool
    speech_final: bool


class TranscriptionErrorPayload(BaseModel):
    """Error payload for transcription stream."""

    error: str
    code: str | None = None
