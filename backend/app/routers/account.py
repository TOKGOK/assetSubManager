from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.models.common import ok, error
from backend.app.models.transaction import CreateAccountRequest, UpdateAccountRequest
from backend.app.services.account import AccountService


def create_account_router(svc: AccountService) -> APIRouter:
    router = APIRouter(tags=["账户管理"])

    @router.get("/", summary="获取账户列表")
    def list_accounts(active_only: bool = False):
        return ok(svc.list_all(active_only=active_only))

    @router.get("/{id}", summary="获取账户详情")
    def get_account(id: int):
        try:
            return ok(svc.get_by_id(id))
        except ValueError:
            raise HTTPException(404, detail=error(40401, f"Account {id} not found"))

    @router.post("/", status_code=201, summary="创建账户")
    def create_account(req: CreateAccountRequest):
        account = svc.create(
            name=req.name, type=req.type, balance=req.balance,
            icon=req.icon, notes=req.notes, sort_order=req.sort_order,
        )
        return ok(account)

    @router.put("/{id}", summary="更新账户")
    def update_account(id: int, req: UpdateAccountRequest):
        try:
            svc.update(id, req)
            return ok()
        except ValueError:
            raise HTTPException(404, detail=error(40401, f"Account {id} not found"))

    @router.delete("/{id}", summary="删除账户")
    def delete_account(id: int):
        try:
            svc.delete(id)
            return ok()
        except ValueError:
            raise HTTPException(404, detail=error(40401, f"Account {id} not found"))

    return router
