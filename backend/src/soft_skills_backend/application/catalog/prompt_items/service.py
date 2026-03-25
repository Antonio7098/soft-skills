"""Prompt item catalog service facade."""

from soft_skills_backend.application.catalog.service import CatalogService

PromptItemService = CatalogService

__all__ = ["PromptItemService"]
