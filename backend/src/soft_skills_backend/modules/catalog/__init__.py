"""Catalog application package."""

from soft_skills_backend.modules.catalog.contracts.collection_commands import (
    ChatCollectionGenerationCommand,
    CollectionCreateCommand,
    CollectionGenerationCounts,
    CollectionLifecycleCommand,
    CollectionListFilters,
    CollectionSaveCommand,
    CollectionUpdateCommand,
    StructuredCollectionGenerationCommand,
)
from soft_skills_backend.modules.catalog.contracts.collection_views import (
    CollectionGenerationView,
    CollectionView,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_commands import (
    PromptItemCreateCommand,
    PromptItemUpdateCommand,
)
from soft_skills_backend.modules.catalog.contracts.prompt_item_views import PromptItemView
from soft_skills_backend.modules.catalog.contracts.scenario_commands import (
    MockCompanyInput,
    MockPersonInput,
    ScenarioCreateCommand,
    ScenarioSupportingArtifactInput,
    ScenarioUpdateCommand,
)
from soft_skills_backend.modules.catalog.contracts.scenario_views import (
    MockCompanyView,
    MockPersonView,
    ScenarioSupportingArtifactView,
    ScenarioView,
)
from soft_skills_backend.modules.catalog.use_cases.catalog_service import CatalogService

__all__ = [
    "CatalogService",
    "ChatCollectionGenerationCommand",
    "CollectionCreateCommand",
    "CollectionGenerationCounts",
    "CollectionGenerationView",
    "CollectionLifecycleCommand",
    "CollectionListFilters",
    "CollectionSaveCommand",
    "CollectionUpdateCommand",
    "CollectionView",
    "CollectionService",
    "MockCompanyInput",
    "MockCompanyView",
    "MockPersonInput",
    "MockPersonView",
    "PromptItemCreateCommand",
    "PromptItemUpdateCommand",
    "PromptItemView",
    "PromptItemService",
    "ScenarioCreateCommand",
    "ScenarioSupportingArtifactInput",
    "ScenarioSupportingArtifactView",
    "ScenarioUpdateCommand",
    "ScenarioView",
    "ScenarioService",
    "StructuredCollectionGenerationCommand",
]
