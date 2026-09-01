from __future__ import annotations

from backend.app.repositories.subscription_period import SubscriptionPeriodRepo
from backend.app.repositories.audit import AuditRepo


class SubscriptionPeriodService:
    def __init__(self, repo: SubscriptionPeriodRepo, audit_repo: AuditRepo):
        self.repo = repo
        self.audit_repo = audit_repo

    def list_all(self) -> list[dict]:
        """获取所有周期配置"""
        periods = self.repo.list_all()
        return [self._format_period(p) for p in periods]

    def get_by_id(self, period_id: int) -> dict | None:
        """根据 ID 获取周期配置"""
        period = self.repo.get_by_id(period_id)
        if not period:
            return None
        return self._format_period(period)

    def create(self, name: str, rule_type: str, **kwargs) -> dict:
        """创建周期配置"""
        period = self.repo.create(
            name=name,
            rule_type=rule_type,
            **kwargs,
        )
        self.audit_repo.log(
            entity_type="subscription_period",
            entity_id=period["id"],
            action="create",
            changed_fields={"name": name},
        )
        return self._format_period(period)

    def update(self, period_id: int, **kwargs) -> dict | None:
        """更新周期配置"""
        period = self.repo.get_by_id(period_id)
        if not period:
            return None

        # 检查是否是默认配置
        if period["is_default"]:
            # 默认配置只允许更新名称和周期参数，不允许更新 rule_type
            kwargs.pop("rule_type", None)

        updated = self.repo.update(period_id, **kwargs)
        if updated:
            self.audit_repo.log(
                entity_type="subscription_period",
                entity_id=period_id,
                action="update",
                changed_fields=kwargs,
            )
        return self._format_period(updated) if updated else None

    def delete(self, period_id: int) -> bool:
        """删除周期配置"""
        period = self.repo.get_by_id(period_id)
        if not period:
            return False

        success = self.repo.delete(period_id)
        if success:
            self.audit_repo.log(
                entity_type="subscription_period",
                entity_id=period_id,
                action="delete",
            )
        return success

    def calculate_next_renewal(self, period_id: int, from_date: str) -> str:
        """计算下次续费日期"""
        return self.repo.calculate_next_renewal(period_id, from_date)

    def _format_period(self, period: dict) -> dict:
        """格式化周期配置（转换 is_default 为 bool）"""
        return {
            **period,
            "is_default": bool(period["is_default"]),
        }
