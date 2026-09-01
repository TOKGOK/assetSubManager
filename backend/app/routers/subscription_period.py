from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.models.common import ok, error
from backend.app.models.subscription_period import (
    CreateSubscriptionPeriodRequest,
    UpdateSubscriptionPeriodRequest,
)
from backend.app.services.subscription_period import SubscriptionPeriodService


# @deprecated Subscription periods may be managed via the unified category/asset-type system.
# This router is kept for backward compatibility and will be removed in a future release.
def create_subscription_period_router(svc: SubscriptionPeriodService) -> APIRouter:
    router = APIRouter(tags=["订阅周期配置"])

    @router.get("/", summary="获取所有订阅周期配置")
    def list_periods():
        periods = svc.list_all()
        return ok(periods)

    @router.get("/{period_id}", summary="获取单个订阅周期配置")
    def get_period(period_id: int):
        period = svc.get_by_id(period_id)
        if not period:
            raise HTTPException(status_code=404, detail=error(40401, "Period not found"))
        return ok(period)

    @router.post("/", status_code=201, summary="创建订阅周期配置")
    def create_period(req: CreateSubscriptionPeriodRequest):
        period = svc.create(
            name=req.name,
            rule_type=req.rule_type,
            interval_days=req.interval_days,
            interval_hours=req.interval_hours,
            month_day=req.month_day,
            month=req.month,
            day=req.day,
        )
        return ok(period)

    @router.put("/{period_id}", summary="更新订阅周期配置")
    def update_period(period_id: int, req: UpdateSubscriptionPeriodRequest):
        updates = req.model_dump(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail=error(40001, "No fields to update"))

        period = svc.update(period_id, **updates)
        if not period:
            raise HTTPException(status_code=404, detail=error(40401, "Period not found"))
        return ok(period)

    @router.delete("/{period_id}", summary="删除订阅周期配置")
    def delete_period(period_id: int):
        try:
            success = svc.delete(period_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=error(40002, str(e)))

        if not success:
            raise HTTPException(status_code=404, detail=error(40401, "Period not found"))
        return ok({"deleted": True})

    @router.get("/{period_id}/calculate-next-renewal", summary="计算下次续费日期")
    def calculate_next_renewal(period_id: int, from_date: str):
        """
        计算从指定日期开始的下次续费日期
        from_date: 格式 YYYY-MM-DD
        """
        try:
            next_date = svc.calculate_next_renewal(period_id, from_date)
            return ok({"period_id": period_id, "from_date": from_date, "next_renewal": next_date})
        except ValueError as e:
            raise HTTPException(status_code=400, detail=error(40003, str(e)))

    return router
