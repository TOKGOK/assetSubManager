from __future__ import annotations

from fastapi import APIRouter

from backend.app.models.common import ok
from backend.app.services.dashboard import DashboardService


def create_dashboard_router(
    dashboard_svc: DashboardService,
) -> APIRouter:
    router = APIRouter(tags=["仪表盘"])

    @router.get("/", summary="获取仪表盘概览数据",
                description="返回物理资产、虚拟资产、订阅的汇总统计信息")
    def dashboard():
        data = dashboard_svc.get_dashboard_data()
        return ok(data)

    @router.get("/category-stats", summary="按分类统计各模块资产")
    def get_category_stats():
        stats = dashboard_svc.get_category_stats()
        return ok(stats)

    return router
