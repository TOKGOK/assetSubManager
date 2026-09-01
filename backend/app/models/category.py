"""Category — unified categories table ORM model.

The categories table now has a ``type_id`` foreign key pointing to
``asset_types``, so each asset type maintains its own independent category
tree.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.orm_base import Base


# ---------------------------------------------------------------------------
# SQLAlchemy ORM model
# ---------------------------------------------------------------------------

class CategoryORM(Base):
    """统一分类表 ORM 模型（通过 type_id 区分所属资产类型）."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("asset_types.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), default=None
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # Relationships
    asset_type: Mapped["AssetTypeORM"] = relationship(  # noqa: F821
        back_populates="categories", lazy="selectin"
    )
    assets: Mapped[list["AssetORM"]] = relationship(  # noqa: F821
        back_populates="category", lazy="selectin"
    )
    children: Mapped[list["CategoryORM"]] = relationship(
        back_populates="parent", lazy="selectin"
    )
    parent: Mapped[Optional["CategoryORM"]] = relationship(
        back_populates="children", remote_side="CategoryORM.id", lazy="selectin"
    )


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CategoryBase(BaseModel):
    """Category 公共字段."""

    type_id: int
    parent_id: int | None = None
    name: str = Field(..., min_length=1, max_length=100)
    icon: str = ""
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    """创建分类请求体."""
    pass


class CategoryUpdate(BaseModel):
    """更新分类请求体（所有字段可选）."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = None
    sort_order: int | None = None
    parent_id: int | None = None


class CategoryResponse(CategoryBase):
    """分类响应体."""

    id: int
    created_at: datetime | str = ""
    children: list["CategoryResponse"] | None = None

    model_config = {"from_attributes": True}
