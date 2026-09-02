from __future__ import annotations

import calendar
import sqlite3
from datetime import datetime, timedelta


class SubscriptionPeriodRepo:
    """Subscription period repository."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def list_all(self) -> list[dict]:
        """获取所有周期配置"""
        cursor = self.db.execute(
            "SELECT * FROM subscription_periods ORDER BY is_default DESC, name ASC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, period_id: int) -> dict | None:
        """根据 ID 获取周期配置"""
        cursor = self.db.execute(
            "SELECT * FROM subscription_periods WHERE id = ?", (period_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_default_periods(self) -> list[dict]:
        """获取系统默认周期配置"""
        cursor = self.db.execute(
            "SELECT * FROM subscription_periods WHERE is_default = 1 ORDER BY name"
        )
        return [dict(row) for row in cursor.fetchall()]

    def create(self, **kwargs) -> dict:
        """创建周期配置"""
        columns = ", ".join(kwargs.keys())
        placeholders = ", ".join(["?"] * len(kwargs))
        values = list(kwargs.values())

        cursor = self.db.execute(
            f"INSERT INTO subscription_periods ({columns}) VALUES ({placeholders})",
            values,
        )
        self.db.commit()
        return self.get_by_id(cursor.lastrowid)

    def update(self, period_id: int, **kwargs) -> dict | None:
        """更新周期配置"""
        if not kwargs:
            return self.get_by_id(period_id)

        # 防止更新 is_default 字段
        kwargs.pop("is_default", None)

        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [period_id]

        self.db.execute(
            f"UPDATE subscription_periods SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        self.db.commit()
        return self.get_by_id(period_id)

    def delete(self, period_id: int) -> bool:
        """删除周期配置（不允许删除系统默认配置）"""
        period = self.get_by_id(period_id)
        if not period:
            return False
        if period["is_default"]:
            raise ValueError("Cannot delete default period configuration")

        self.db.execute(
            "DELETE FROM subscription_periods WHERE id = ? AND is_default = 0",
            (period_id,),
        )
        self.db.commit()
        return True

    def calculate_next_renewal(self, period_id: int, from_date: str) -> str:
        """根据周期配置计算下次续费日期"""
        period = self.get_by_id(period_id)
        if not period:
            raise ValueError(f"Period {period_id} not found")

        start = datetime.strptime(from_date, "%Y-%m-%d")

        if period["rule_type"] == "daily_interval":
            if period["interval_days"] == 0:
                return ""  # 一次性
            next_date = start + timedelta(days=period["interval_days"])
            return next_date.strftime("%Y-%m-%d")

        elif period["rule_type"] == "monthly_day":
            # month_day > 0: 每月固定 X 日（如"每月15日"）
            # month_day == 0: 按开始日期的天数（如开始 8-27 → 每月 27 日）
            if period["month_day"] and period["month_day"] > 0:
                day = period["month_day"]
            else:
                day = start.day
            # 计算下个月的该日
            if start.month == 12:
                next_month = datetime(start.year + 1, 1, 1)
            else:
                next_month = datetime(start.year, start.month + 1, 1)
            # 处理月末日期（如 1月31日 → 2月28日）
            max_day = calendar.monthrange(next_month.year, next_month.month)[1]
            day = min(day, max_day)
            next_date = datetime(next_month.year, next_month.month, day)
            return next_date.strftime("%Y-%m-%d")

        elif period["rule_type"] == "yearly_date":
            # month > 0 且 day > 0: 每年固定 X月X日（如"每年3月1日"）
            # 否则: 按开始日期的月日（如开始 8-27 → 次年 8-27）
            if period["month"] and period["month"] > 0 and period["day"] and period["day"] > 0:
                month = period["month"]
                day = period["day"]
            else:
                month = start.month
                day = start.day
            next_year = start.year + 1
            max_day = calendar.monthrange(next_year, month)[1]
            day = min(day, max_day)
            next_date = datetime(next_year, month, day)
            return next_date.strftime("%Y-%m-%d")

        elif period["rule_type"] == "custom":
            # 自定义：days + hours
            total_hours = period["interval_days"] * 24 + period["interval_hours"]
            if total_hours == 0:
                return ""  # 一次性
            next_date = start + timedelta(hours=total_hours)
            return next_date.strftime("%Y-%m-%d")

        return ""
