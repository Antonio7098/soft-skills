# Media Archive (Audio & Video)

## Purpose

Provide a unified subsystem to ingest, store, and retrieve rich-media attempts
(audio, video) plus transcripts so the platform can support voice/video practice
modes, coach reviews, and longitudinal analysis.

## Goals

- Capture high-fidelity recordings with synchronized transcripts and metadata.
- Keep storage and retrieval contracts consistent across practice modes.
- Make media artifacts addressable by assessments, progression history, and the
  forthcoming knowledge graph.
- Enforce privacy, retention, and deletion policies per learner preference and
  regulatory requirements.

## Non-Goals

- Live streaming (handled by the live chat / realtime service).
- Coach-facing editing or advanced video production features.
- Automated sentiment or emotion analysis (possible future add-on).

## Functional Requirements

1. **Recording:** Web and mobile clients can opt into audio or video capture
   during an attempt. The capture module buffers locally and uploads chunks via a
   resumable protocol to avoid data loss.
2. **Transcription:** Audio/video attempts are transcribed (LLM or ASR pipelines)
   into time-coded text that preserves speaker turns and confidence scores.
3. **Storage:** Media, transcript, and metadata are atomically committed to an
   `AttemptMedia` record with references to the base `Attempt` and `Trace`.
4. **Access Control:** Learners can replay their own media. Coaches/Admins need a
   scoped permission granting read access, with watermarking in UI.
5. **Retention:** Defaults to 12 months, configurable per cohort or enterprise.
   Learners can request deletion, triggering a soft-delete and tombstone record
   so assessment history remains explainable.
6. **Export:** Provide signed URLs or streaming tokens for download when legally
   required (e.g., learner data export).

## Data Model Additions

- `AttemptMedia` (new entity)
  - `attempt_id`
  - `media_type` (audio/video)
  - `storage_uri`
  - `duration_seconds`
  - `transcript_id`
  - `transcription_confidence`
  - `processing_status` (pending, complete, failed)
  - `retention_expiry`
  - `privacy_flags`
- `Transcript`
  - `transcript_id`
  - `text_blob` or segmented structure
  - `word_timestamps`
  - `speaker_labels`
  - `source_model`
  - `redaction_status`

## Pipeline Overview

```
Client Capture SDK
  ↓ chunked upload (HTTPS/WebRTC)
Ingest Gateway (pre-signed URLs, auth)
  ↓ object storage (S3-compatible)
Media Processor (transcode, normalize levels)
  ↓ transcription service (internal or vendor)
Metadata Writer (stores AttemptMedia + Transcript)
  ↓ assessment + knowledge graph subscribers
```

## Observability

- Emit ingest metrics (success/failure per medium, size, duration).
- Track transcription latency and word-error rates.
- Alert when storage growth exceeds projections or when transcripts fall below
  confidence thresholds.

## Privacy & Compliance

- Honor GDPR/CCPA deletion requests via media tombstones and audit trail.
- Encrypt media at rest with per-tenant keys if enterprise contract requires it.
- Support selective redaction (e.g., names) within transcripts prior to coach
  sharing.

## Dependencies

1. Client capture SDK with fallback to audio-only for bandwidth-constrained users.
2. Object storage tier with lifecycle policies.
3. Updated assessment pipeline to reference `AttemptMedia` when generating
   explanations (e.g., link to transcript snippets).
4. Knowledge graph ingestion jobs to attach media nodes to attempts and skills.

## Open Questions

- Should we provide automated redaction or require manual review?
- Do we offer offline recording with later upload?
- How do we surface storage costs to admins for budgeting?
- What is the policy for sharing recordings with peers or mentors outside the
  platform?
