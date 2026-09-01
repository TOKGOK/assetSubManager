"""Asset — unified assets table ORM model and Pydantic schemas.

This is the **new** unified asset model that replaces the legacy per-type
tables (``assets`` for physical, ``virtual_assets``, ``subscriptions``).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.orm_base import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM model
# ---------------------------------------------------------------------------

class AssetORM(Base):
    """统一资产表 ORM 模型."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("asset_types.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), default=None
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    custom_data: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    asset_type: Mapped["AssetTypeORM"] = relationship(  # noqa: F821
        back_populates="assets", lazy="selectin"
    )
    category: Mapped[Optional["CategoryORM"]] = relationship(  # noqa: F821
        back_populates="assets", lazy="selectin"
    )


# ---------------------------------------------------------------------------
# Pydantic schemas (for API request / response)
# ---------------------------------------------------------------------------

class AssetBase(BaseModel):
    """Asset 公共字段."""

    type_id: int
    category_id: int | None = None
    name: str = Field(..., min_length=1, max_length=200)
    custom_data: dict[str, Any] | None = None


class AssetCreate(AssetBase):
    """创建资产请求体."""
    pass


class AssetUpdate(BaseModel):
    """更新资产请求体（所有字段可选）."""

    type_id: int | None = None
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    custom_data: dict[str, Any] | None = None


class AssetResponse(AssetBase):
    """资产响应体."""

    id: int
    created_at: datetime | str = ""
    updated_at: datetime | str = ""

    # Optional nested info populated by service layer
    type_name: str = ""
    type_icon: str = ""
    category_name: str = ""
    computed_fields: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class AssetListFilter(BaseModel):
    """资产列表筛选条件."""

    type_id: int | None = None
    category_id: int | None = None
    search: str = ""
    sort_by: str = ""
    sort_order: str = "asc"
    page: int = 1
    page_size: int = 20
