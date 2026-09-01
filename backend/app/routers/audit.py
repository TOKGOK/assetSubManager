from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.models.common import ok_list
from backend.app.repositories.audit import AuditRepo


def create_audit_router(repo: AuditRepo) -> APIRouter:
    router = APIRouter(tags=["审计日志"])

    @router.get("/", summary="获取审计日志列表", description="支持按实体类型、操作类型筛选，分页查询")
    def list_logs(
        entity_type: str = "",
        action: str = "",
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        items, total = repo.list(entity_type, action, page, page_size)
        return ok_list(items, total, page, page_size)

    return router
