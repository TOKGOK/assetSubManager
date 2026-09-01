from __future__ import annotations

from backend.app.repositories.asset import AssetRepo


# System asset type IDs (defined in database.py)
TYPE_PHYSICAL = 1
TYPE_VIRTUAL = 2
TYPE_SUBSCRIPTION = 3


class DashboardService:
    """聚合所有资产类型的统计数据（使用统一 AssetRepo）。"""

    def __init__(
        self,
        asset_repo: AssetRepo,
        subscription_service=None,
    ):
        self.asset_repo = asset_repo
        self.subscription_service = subscription_service

    def get_dashboard_data(self) -> dict:
        """获取仪表盘汇总数据，包含各模块的统计信息。"""
        # ── 物理资产统计 ──
        physical_count = self.asset_repo.count_by_type(TYPE_PHYSICAL)
        physical_total_value = self.asset_repo.sum_custom_field(TYPE_PHYSICAL, "current_value")
        physical_status_counts = self.asset_repo.status_counts_by_type(TYPE_PHYSICAL)

        # ── 虚拟资产统计 ──
        virtual_count = self.asset_repo.count_by_type(TYPE_VIRTUAL)
        virtual_status_counts = self.asset_repo.status_counts_by_type(TYPE_VIRTUAL)

        # ── 订阅统计 ──
        subscription_count = self.asset_repo.count_by_type(TYPE_SUBSCRIPTION)
        upcoming = self.asset_repo.upcoming_renewals(TYPE_SUBSCRIPTION, 30)
        monthly_total = self._calc_monthly_total()

        return {
            # 向后兼容字段（原有 dashboard API 的字段）
            "total_count": physical_count,
            "total_value": physical_total_value,
            "status_counts": physical_status_counts,
            "monthly_subscription": monthly_total,
            "upcoming_subscriptions": upcoming,
            # 分模块统计
            "physical_assets": {
                "total_count": physical_count,
                "total_value": physical_total_value,
                "status_counts": physical_status_counts,
            },
            "virtual_assets": {
                "total_count": virtual_count,
                "status_counts": virtual_status_counts,
            },
            "subscriptions": {
                "total_count": subscription_count,
                "monthly_total": monthly_total,
                "upcoming_renewals": upcoming,
            },
        }

    def get_category_stats(self) -> dict:
        """获取各模块分类统计。"""
        return {
            "physical": self.asset_repo.get_category_stats(TYPE_PHYSICAL),
            "virtual": self.asset_repo.get_category_stats(TYPE_VIRTUAL),
            "subscription": self.asset_repo.get_category_stats(TYPE_SUBSCRIPTION),
        }

    # ── 内部辅助 ──────────────────────────────────────────

    def _calc_monthly_total(self) -> float:
        """将所有活跃订阅的周期折算为月度金额。"""
        if self.subscription_service is not None:
            return self.subscription_service.monthly_total()
        # Fallback: calculate directly from assets table
        return self.asset_repo.monthly_subscription_total(TYPE_SUBSCRIPTION)
