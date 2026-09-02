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
        # ── 各类型统计（金额字段统一为 value） ──
        physical_count = self.asset_repo.count_by_type(TYPE_PHYSICAL)
        physical_status_counts = self.asset_repo.status_counts_by_type(TYPE_PHYSICAL)
        physical_total_value = self.asset_repo.sum_custom_field(TYPE_PHYSICAL, "value")

        virtual_count = self.asset_repo.count_by_type(TYPE_VIRTUAL)
        virtual_status_counts = self.asset_repo.status_counts_by_type(TYPE_VIRTUAL)
        virtual_total_value = self.asset_repo.sum_custom_field(TYPE_VIRTUAL, "value")

        subscription_count = self.asset_repo.count_by_type(TYPE_SUBSCRIPTION)
        subscription_total_value = self.asset_repo.sum_custom_field(TYPE_SUBSCRIPTION, "value")
        upcoming = self.asset_repo.upcoming_renewals(TYPE_SUBSCRIPTION, 30)
        monthly_total = self._calc_monthly_total()

        return {
            "total_count": physical_count + virtual_count + subscription_count,
            "total_value": physical_total_value + virtual_total_value + subscription_total_value,
            "status_counts": physical_status_counts,
            "monthly_subscription": monthly_total,
            "upcoming_subscriptions": upcoming,
            "physical_assets": {
                "total_count": physical_count,
                "total_value": physical_total_value,
                "status_counts": physical_status_counts,
            },
            "virtual_assets": {
                "total_count": virtual_count,
                "total_value": virtual_total_value,
                "status_counts": virtual_status_counts,
            },
            "subscriptions": {
                "total_count": subscription_count,
                "total_value": subscription_total_value,
                "monthly_total": monthly_total,
                "upcoming_renewals": upcoming,
            },
        }

    def get_category_stats(self) -> list:
        """获取按资产类型（实体/虚拟/订阅）聚合的统计，返回 3 条记录。"""
        result = []
        for type_key, type_id in [
            ("physical", TYPE_PHYSICAL),
            ("virtual", TYPE_VIRTUAL),
            ("subscription", TYPE_SUBSCRIPTION),
        ]:
            count = self.asset_repo.count_by_type(type_id)
            total_value = self.asset_repo.sum_custom_field(type_id, "value")
            result.append({
                "name": type_key,
                "count": count,
                "total_value": total_value,
            })
        return result

    # ── 内部辅助 ──────────────────────────────────────────

    def _calc_monthly_total(self) -> float:
        """将所有活跃订阅的周期折算为月度金额。"""
        if self.subscription_service is not None:
            return self.subscription_service.monthly_total()
        return self.asset_repo.monthly_subscription_total(TYPE_SUBSCRIPTION)
