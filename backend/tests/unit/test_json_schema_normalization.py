from __future__ import annotations

from soft_skills_backend.shared.ports.models import normalize_strict_json_schema


def test_normalize_strict_json_schema_preserves_optional_properties() -> None:
    schema = {
        "type": "object",
        "properties": {
            "required_field": {"type": "string"},
            "optional_field": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["required_field"],
    }

    normalized = normalize_strict_json_schema(schema)

    assert normalized["additionalProperties"] is False
    assert normalized["required"] == ["required_field"]
    assert "optional_field" not in normalized["required"]
