"""Evaluation command contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class EvaluationRunCommand(BaseModel):
    """Admin-triggered evaluation command."""

    suite_id: str
    model_slugs: list[str] = Field(default_factory=list)
    case_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize(self) -> EvaluationRunCommand:
        self.suite_id = self.suite_id.strip()
        if not self.suite_id:
            raise ValueError("suite_id must not be blank")
        self.model_slugs = [model_slug.strip() for model_slug in self.model_slugs if model_slug.strip()]
        self.case_ids = [case_id.strip() for case_id in self.case_ids if case_id.strip()]
        self.tags = [tag.strip() for tag in self.tags if tag.strip()]
        return self
