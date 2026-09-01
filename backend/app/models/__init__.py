"""Models package — re-exports ORM and Pydantic models for convenience."""

# ORM models (SQLAlchemy)
from backend.app.models.asset import AssetORM
from backend.app.models.asset_type import AssetTypeORM
from backend.app.models.category import CategoryORM

# Pydantic schemas — AssetType
from backend.app.models.asset_type import (
    AssetTypeBase,
    AssetTypeCreate,
    AssetTypeResponse,
    AssetTypeUpdate,
    FieldConfig,
    FieldDefinition,
)

# Pydantic schemas — Asset (unified)
from backend.app.models.asset import (
    AssetBase,
    AssetCreate,
    AssetListFilter,
    AssetResponse,
    AssetUpdate,
)

# Pydantic schemas — Category (unified)
from backend.app.models.category import (
    CategoryBase,
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)

__all__ = [
    # ORM
    "AssetTypeORM",
    "AssetORM",
    "CategoryORM",
    # Pydantic — AssetType
    "AssetTypeBase",
    "AssetTypeCreate",
    "AssetTypeUpdate",
    "AssetTypeResponse",
    "FieldDefinition",
    "FieldConfig",
    # Pydantic — Asset
    "AssetBase",
    "AssetCreate",
    "AssetUpdate",
    "AssetResponse",
    "AssetListFilter",
    # Pydantic — Category
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
]
