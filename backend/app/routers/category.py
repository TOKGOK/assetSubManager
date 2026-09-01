"""Category router — unified category API scoped by asset type.

Endpoints
---------
GET    /api/v1/asset-types/{type_id}/categories/   list tree
POST   /api/v1/asset-types/{type_id}/categories/   create
GET    /api/v1/categories/{id}                     get by id
PUT    /api/v1/categories/{id}                     update
DELETE /api/v1/categories/{id}                     delete
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.models.common import ok, error
from backend.app.services.category import CategoryService


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: int | None = None
    icon: str = ""
    sort_order: int = 0


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = None
    sort_order: int | None = None
    parent_id: int | None = None


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------

def create_category_router(svc: CategoryService) -> APIRouter:
    """Return a router with **all** unified category endpoints.

    Because the API has two different URL prefixes we create two routers and
    merge them into a single parent.  Callers should mount the returned
    routers separately — see ``main.py`` for the registration pattern.
    """
    # We return a wrapper that holds two sub-routers.  The caller (main.py)
    # will include each sub-router at the right prefix.  To keep things
    # simple we instead expose two factory functions.
    raise NotImplementedError(
        "Use create_type_scoped_router and create_detail_router instead."
    )


def create_type_scoped_router(svc: CategoryService) -> APIRouter:
    """Endpoints mounted at ``/api/v1/asset-types/{type_id}/categories``."""
    router = APIRouter(tags=["统一分类管理"])

    @router.get("/", summary="获取指定资产类型的分类树")
    def list_categories(type_id: int):
        try:
            return ok(svc.list_tree(type_id))
        except ValueError as e:
            raise HTTPException(404, detail=error(40404, str(e)))

    @router.post("/", status_code=201, summary="在指定资产类型下创建分类")
    def create_category(type_id: int, req: CategoryCreateRequest):
        try:
            cat = svc.create(
                type_id, req.name, req.parent_id, req.icon, req.sort_order,
            )
            return ok(cat)
        except ValueError as exc:
            msg = str(exc)
            if "not found" in msg:
                raise HTTPException(404, detail=error(40404, msg))
            raise HTTPException(400, detail=error(40006, msg))

    return router


def create_detail_router(svc: CategoryService) -> APIRouter:
    """Endpoints mounted at ``/api/v1/categories``."""
    router = APIRouter(tags=["统一分类管理"])

    @router.get("/{id}", summary="获取单个分类详情")
    def get_category(id: int):
        try:
            return ok(svc.get_by_id(id))
        except ValueError:
            raise HTTPException(404, detail=error(40401, f"Category {id} not found"))

    @router.put("/{id}", summary="更新分类信息")
    def update_category(id: int, req: CategoryUpdateRequest):
        try:
            cat = svc.update(
                id,
                name=req.name,
                icon=req.icon,
                sort_order=req.sort_order,
                parent_id=req.parent_id,
            )
            return ok(cat)
        except ValueError as exc:
            msg = str(exc)
            if "not found" in msg:
                raise HTTPException(404, detail=error(40401, msg))
            raise HTTPException(400, detail=error(40005, msg))

    @router.delete("/{id}", summary="删除分类", description="若分类下存在子分类或关联资产将返回错误")
    def delete_category(id: int):
        try:
            svc.delete(id)
            return ok()
        except ValueError as exc:
            msg = str(exc)
            if "not found" in msg:
                raise HTTPException(404, detail=error(40401, msg))
            raise HTTPException(400, detail=error(40004, msg))

    return router
