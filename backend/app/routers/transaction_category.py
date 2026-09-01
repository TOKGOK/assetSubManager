from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.app.models.common import ok, ok_list, error
from backend.app.models.transaction import (
    CreateTransactionCategoryRequest,
    UpdateTransactionCategoryRequest,
)
from backend.app.services.transaction_category import TransactionCategoryService


def create_transaction_category_router(
    svc: TransactionCategoryService,
) -> APIRouter:
    router = APIRouter(tags=["记账分类"])

    @router.get("/", summary="获取所有记账分类列表")
    def list_categories(type: str = ""):
        if type:
            return ok(svc.list_by_type(type))
        return ok(svc.list_all())

    @router.post("/", status_code=201, summary="创建记账分类")
    def create_category(req: CreateTransactionCategoryRequest):
        cat = svc.create(
            name=req.name, icon=req.icon, type=req.type,
            parent_id=req.parent_id, sort_order=req.sort_order,
        )
        return ok(cat)

    @router.put("/{id}", summary="更新记账分类")
    def update_category(id: int, req: UpdateTransactionCategoryRequest):
        try:
            svc.update(id, req)
            return ok()
        except ValueError:
            raise HTTPException(404, detail=error(40401, f"TransactionCategory {id} not found"))

    @router.delete("/{id}", summary="删除记账分类")
    def delete_category(id: int):
        try:
            svc.delete(id)
            return ok()
        except ValueError:
            raise HTTPException(404, detail=error(40401, f"TransactionCategory {id} not found"))

    return router
