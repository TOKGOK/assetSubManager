"""Subscription reminders router.

Provides upcoming-renewal reminders for subscription-type assets.
Mounted at ``/api/v1/subscriptions``.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.models.common import ok
from backend.app.repositories.asset import AssetRepo


TYPE_SUBSCRIPTION = 3


def create_subscription_router(asset_repo: AssetRepo) -> APIRouter:
    router = APIRouter(tags=["订阅"])

    @router.get("/reminders", summary="获取即将到期的订阅提醒")
    def get_reminders(
        days: int = Query(30, ge=1, le=365, description="提前提醒天数"),
    ):
        items = asset_repo.upcoming_renewals(TYPE_SUBSCRIPTION, days)
        return ok(items)

    return router
