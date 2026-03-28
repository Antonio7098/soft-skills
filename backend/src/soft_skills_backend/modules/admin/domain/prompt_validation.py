"""Prompt validation subpipeline for syntax, variables, and output format."""

from __future__ import annotations

import re
from typing import Any


class PromptValidationError(Exception):
    """Raised when prompt validation fails."""

    def __init__(self, stage: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.stage = stage
        self.message = message
        self.details = details or {}
        super().__init__(f"[{stage}] {message}")


def validate_syntax(template: str) -> None:
    """Validate basic template syntax - check for balanced braces."""
    open_count = template.count("{")
    close_count = template.count("}")
    if open_count != close_count:
        raise PromptValidationError(
            stage="syntax",
            message="Unbalanced braces in template",
            details={"open_braces": open_count, "close_braces": close_count},
        )


def validate_variables(
    template: str,
    variables: dict[str, Any],
    variables_schema: dict[str, Any],
) -> None:
    """Validate that all template variables are defined in variables_schema."""
    template_vars = extract_template_variables(template)
    required_vars = set(variables_schema.get("required", []))
    schema_props = set(variables_schema.get("properties", {}))

    missing = template_vars - set(variables.keys())
    if missing:
        raise PromptValidationError(
            stage="variables",
            message="Template references undefined variables",
            details={"missing_variables": list(missing)},
        )

    undeclared_in_schema = template_vars - schema_props
    if undeclared_in_schema:
        raise PromptValidationError(
            stage="variables",
            message="Template variables are missing from variables_schema.properties",
            details={"undeclared_variables": list(undeclared_in_schema)},
        )

    unspecified_required = required_vars - template_vars
    if unspecified_required:
        raise PromptValidationError(
            stage="variables",
            message="Schema declares required variables not used in template",
            details={"unspecified_required": list(unspecified_required)},
        )


def validate_output_format(template: str, output_schema: dict[str, Any] | None) -> None:
    """Validate that template includes required JSON output fields if output_schema is defined."""
    if output_schema is None:
        return

    required_fields = output_schema.get("required", [])
    if not required_fields:
        return

    for field in required_fields:
        field_pattern = rf'("{field}"\s*:|-\s+{field}\s*:)'
        if not re.search(field_pattern, template):
            raise PromptValidationError(
                stage="output_format",
                message=f"Required output field '{field}' not found in template",
                details={"missing_field": field, "required_fields": required_fields},
            )


def validate_prompt(
    template: str,
    variables: dict[str, Any],
    variables_schema: dict[str, Any],
    output_schema: dict[str, Any] | None,
) -> None:
    """
    Run the full prompt validation subpipeline.

    Stages:
    1. Syntax check - balanced braces
    2. Variable check - template variables match schema
    3. Output format check - required JSON fields present if output_schema defined

    Raises PromptValidationError on first failure.
    """
    validate_syntax(template)
    validate_variables(template, variables, variables_schema)
    rendered_content = template.format(**variables)
    validate_output_format(rendered_content, output_schema)


def validate_prompt_definition(
    template: str,
    variables_schema: dict[str, Any],
) -> None:
    """Validate a prompt definition before it is stored."""

    validate_syntax(template)
    template_vars = extract_template_variables(template)
    required_vars = set(variables_schema.get("required", []))
    schema_props = set(variables_schema.get("properties", {}))

    undeclared_in_schema = template_vars - schema_props
    if undeclared_in_schema:
        raise PromptValidationError(
            stage="variables",
            message="Template variables are missing from variables_schema.properties",
            details={"undeclared_variables": list(undeclared_in_schema)},
        )

    unused_required = required_vars - template_vars
    if unused_required:
        raise PromptValidationError(
            stage="variables",
            message="Schema declares required variables not used in template",
            details={"unused_required_variables": list(unused_required)},
        )


def extract_template_variables(template: str) -> set[str]:
    """Extract Stageflow-style named format variables from a template."""

    return set(re.findall(r"\{(\w+)\}", template))
