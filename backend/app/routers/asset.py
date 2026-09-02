"""Unified asset REST API router."""

from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query

from backend.app.models.common import ok, ok_list, error
from backend.app.models.asset import AssetCreate, AssetUpdate
from backend.app.services.asset import AssetService, ValidationError


def create_asset_router(svc: AssetService) -> APIRouter:
    router = APIRouter(tags=["统一资产管理"])

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    @router.get("/", summary="获取资产列表", description="支持按类型、分类、状态筛选，关键词搜索，分页")
    def list_assets(
        type_ids: str = Query(
            "",
            description="逗号分隔的 type_id 列表，如 '1,2,3'",
        ),
        category_id: int | None = Query(None, description="分类 ID"),
        search: str = Query("", description="搜索关键词（搜索 name 和 custom_data）"),
        status: str = Query("", description="状态筛选（active/sold/disposed/cancelled/expired）"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    ):
        ids: list[int] | None = None
        if type_ids:
            try:
                ids = [int(x.strip()) for x in type_ids.split(",") if x.strip()]
            except ValueError:
                raise HTTPException(
                    400, detail=error(40001, "type_ids 格式错误，应为逗号分隔的数字")
                )
            if not ids:
                ids = None

        items, total = svc.list(
            type_ids=ids,
            category_id=category_id,
            search=search,
            status=status,
            page=page,
            page_size=page_size,
        )
        return ok_list(items, total, page, page_size)

    # ------------------------------------------------------------------
    # Detail
    # ------------------------------------------------------------------

    @router.get("/{id}", summary="获取资产详情")
    def get_asset(id: int):
        try:
            return ok(svc.get_by_id(id))
        except ValueError:
            raise HTTPException(404, detail=error(40401, f"Asset {id} not found"))

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @router.post("/", status_code=201, summary="创建资产")
    def create_asset(req: AssetCreate):
        try:
            asset = svc.create(
                type_id=req.type_id,
                name=req.name,
                category_id=req.category_id,
                custom_data=req.custom_data,
            )
            return ok(asset)
        except ValueError as exc:
            raise HTTPException(400, detail=error(40002, str(exc)))
        except ValidationError as exc:
            raise HTTPException(400, detail=error(40003, str(exc)))

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @router.put("/{id}", summary="更新资产")
    def update_asset(id: int, req: AssetUpdate):
        # Reject type_id modification
        if req.type_id is not None:
            raise HTTPException(
                400, detail=error(40004, "资产类型不可修改")
            )
        try:
            asset = svc.update(
                id,
                name=req.name,
                category_id=req.category_id,
                custom_data=req.custom_data,
            )
            return ok(asset)
        except ValueError as exc:
            msg = str(exc)
            if "not found" in msg.lower():
                raise HTTPException(404, detail=error(40401, msg))
            raise HTTPException(400, detail=error(40005, msg))
        except ValidationError as exc:
            raise HTTPException(400, detail=error(40003, str(exc)))

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @router.delete("/{id}", summary="删除资产")
    def delete_asset(id: int):
        try:
            svc.delete(id)
            return ok()
        except ValueError:
            raise HTTPException(404, detail=error(40401, f"Asset {id} not found"))

    # ------------------------------------------------------------------
    # Batch delete
    # ------------------------------------------------------------------

    @router.post("/batch-delete", summary="批量删除资产")
    def batch_delete_assets(ids: list[int] = Body(..., embed=True)):
        """批量删除多个资产。返回实际删除的数量。"""
        deleted = svc.batch_delete(ids)
        return ok({"deleted": deleted})

    return router
