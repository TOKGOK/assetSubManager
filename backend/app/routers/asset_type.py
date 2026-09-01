"""AssetType RESTful API router."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.models.common import ok, error
from backend.app.models.asset_type import AssetTypeCreate, AssetTypeUpdate
from backend.app.services.asset_type import AssetTypeService


def create_asset_type_router(svc: AssetTypeService) -> APIRouter:
    router = APIRouter(tags=["资产类型管理"])

    # -- list -----------------------------------------------------------------

    @router.get("/", summary="获取资产类型列表")
    def list_asset_types():
        items = svc.list()
        return ok(items)

    # -- create ---------------------------------------------------------------

    @router.post("/", status_code=201, summary="创建资产类型")
    def create_asset_type(req: AssetTypeCreate):
        try:
            fc = (
                req.field_config.model_dump()
                if hasattr(req.field_config, "model_dump")
                else req.field_config
            )
            result = svc.create(
                name=req.name,
                icon=req.icon,
                field_config=fc,
                is_system=req.is_system,
            )
            return ok(result)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=error(40000, str(exc)))

    # -- detail ---------------------------------------------------------------

    @router.get("/{id}", summary="获取资产类型详情")
    def get_asset_type(id: int):
        try:
            return ok(svc.get_by_id(id))
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=error(40400, f"AssetType {id} not found"),
            )

    # -- update ---------------------------------------------------------------

    @router.put("/{id}", summary="更新资产类型")
    def update_asset_type(id: int, req: AssetTypeUpdate):
        update_data = req.model_dump(exclude_unset=True)
        # Convert FieldConfig → dict if needed
        if "field_config" in update_data and update_data["field_config"] is not None:
            fc = update_data["field_config"]
            if hasattr(fc, "model_dump"):
                update_data["field_config"] = fc.model_dump()
        try:
            svc.update(id, **update_data)
            return ok()
        except ValueError as exc:
            msg = str(exc)
            if "not found" in msg:
                raise HTTPException(
                    status_code=404,
                    detail=error(40400, msg),
                )
            raise HTTPException(status_code=400, detail=error(40000, msg))

    # -- delete ---------------------------------------------------------------

    @router.delete("/{id}", summary="删除资产类型")
    def delete_asset_type(id: int):
        try:
            svc.delete(id)
            return ok()
        except ValueError as exc:
            msg = str(exc)
            if "not found" in msg:
                raise HTTPException(
                    status_code=404,
                    detail=error(40400, msg),
                )
            raise HTTPException(status_code=400, detail=error(40000, msg))

    return router
