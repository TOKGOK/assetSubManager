"""AssetType — SQLAlchemy ORM model and Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.orm_base import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM model
# ---------------------------------------------------------------------------

class AssetTypeORM(Base):
    """资产类型定义表 ORM 模型."""

    __tablename__ = "asset_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    icon: Mapped[str | None] = mapped_column(String(50), default="")
    field_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    assets: Mapped[list["AssetORM"]] = relationship(  # noqa: F821 – forward ref
        back_populates="asset_type", lazy="selectin"
    )
    categories: Mapped[list["CategoryORM"]] = relationship(  # noqa: F821
        back_populates="asset_type", lazy="selectin"
    )


# ---------------------------------------------------------------------------
# Pydantic schemas (for API request / response)
# ---------------------------------------------------------------------------

class FieldDefinition(BaseModel):
    """单个字段定义（存在于 field_config.fields 列表中）."""

    key: str
    label: str
    type: str = Field(
        ..., description="字段类型: text, number, boolean, date, datetime, select, textarea, relation, computed"
    )
    required: bool = False
    options: dict[str, Any] | None = None


class FieldConfig(BaseModel):
    """资产类型的字段配置结构."""

    fields: list[FieldDefinition] = []


class AssetTypeBase(BaseModel):
    """AssetType 公共字段."""

    name: str = Field(..., min_length=1, max_length=100)
    icon: str = ""
    field_config: dict[str, Any] | FieldConfig = Field(default_factory=dict)
    is_system: bool = False


class AssetTypeCreate(AssetTypeBase):
    """创建资产类型请求体."""
    pass


class AssetTypeUpdate(BaseModel):
    """更新资产类型请求体（所有字段可选）."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = None
    field_config: dict[str, Any] | FieldConfig | None = None
    is_system: bool | None = None


class AssetTypeResponse(AssetTypeBase):
    """资产类型响应体."""

    id: int
    field_config: dict[str, Any]
    created_at: datetime | str = ""
    updated_at: datetime | str = ""

    model_config = {"from_attributes": True}
