"""Tests for telemetry module."""

from __future__ import annotations

from soft_skills_backend.platform.observability.telemetry import (
    OTEL_TRACE_CONTEXT_HEADER,
    W3C_TRACE_VERSION,
    build_telemetry_config,
    extract_trace_context,
)


class TestBuildTelemetryConfig:
    def test_builds_config_with_all_fields(self) -> None:
        config = build_telemetry_config(
            enabled=True,
            service_name="test-service",
            otlp_endpoint="http://localhost:4317",
        )

        assert config.enabled is True
        assert config.service_name == "test-service"
        assert config.otlp_endpoint == "http://localhost:4317"

    def test_builds_config_with_defaults(self) -> None:
        config = build_telemetry_config(
            enabled=False,
            service_name="test",
            otlp_endpoint=None,
        )

        assert config.enabled is False
        assert config.export_timeout_ms == 30_000


class TestExtractTraceContext:
    def test_extracts_valid_traceparent(self) -> None:
        headers = {
            OTEL_TRACE_CONTEXT_HEADER: "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }
        result = extract_trace_context(headers)

        assert result is not None
        assert "traceparent" in result

    def test_returns_none_for_missing_header(self) -> None:
        headers: dict[str, str] = {}
        result = extract_trace_context(headers)

        assert result is None

    def test_returns_none_for_invalid_version(self) -> None:
        headers = {
            OTEL_TRACE_CONTEXT_HEADER: "01-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        }
        result = extract_trace_context(headers)

        assert result is None

    def test_returns_none_for_empty_traceparent(self) -> None:
        headers = {OTEL_TRACE_CONTEXT_HEADER: ""}
        result = extract_trace_context(headers)

        assert result is None


class TestTelemetryConstants:
    def test_w3c_trace_version(self) -> None:
        assert W3C_TRACE_VERSION == "00"

    def test_otel_trace_context_header(self) -> None:
        assert OTEL_TRACE_CONTEXT_HEADER == "traceparent"
