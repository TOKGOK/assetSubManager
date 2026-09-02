"""Unified asset service layer.

Responsibilities:
* ``custom_data`` validation against the asset-type's ``field_config``
* Computed-field evaluation via :class:`ExpressionEngine`
* Orchestration of repository calls + audit logging
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from backend.app.repositories.asset import AssetRepo
from backend.app.repositories.audit import AuditRepo
from backend.app.services.expression_engine import ExpressionEngine, ExpressionError


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when custom_data fails field_config validation."""

    def __init__(self, errors: list[dict[str, str]]):
        self.errors = errors  # [{"field": "<key>", "message": "<reason>"}]
        parts = [f"{e['field']}: {e['message']}" for e in errors]
        super().__init__("; ".join(parts))


def _validate_field(
    field_def: dict,
    value: Any,
    repo: AssetRepo,
) -> str | None:
    """Validate a single field value.  Returns an error message or *None*."""
    ftype = field_def.get("type", "text")
    opts = field_def.get("options") or {}

    # -- text / textarea ------------------------------------------------
    if ftype in ("text", "textarea"):
        if not isinstance(value, str):
            return "必须是文本字符串"
        max_len = opts.get("maxLength") or opts.get("max_length")
        if max_len is not None and len(value) > int(max_len):
            return f"长度不能超过 {max_len}"
        pattern = opts.get("pattern")
        if pattern and not re.match(pattern, value):
            return f"不匹配格式要求: {pattern}"

    # -- number ---------------------------------------------------------
    elif ftype == "number":
        if not isinstance(value, (int, float)):
            return "必须是数字"
        min_val = opts.get("min")
        max_val = opts.get("max")
        if min_val is not None and value < min_val:
            return f"不能小于 {min_val}"
        if max_val is not None and value > max_val:
            return f"不能大于 {max_val}"

    # -- boolean --------------------------------------------------------
    elif ftype == "boolean":
        if not isinstance(value, bool):
            return "必须是布尔值"

    # -- date -----------------------------------------------------------
    elif ftype == "date":
        if not isinstance(value, str):
            return "必须是日期字符串"
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return "日期格式不正确，应为 YYYY-MM-DD"
        min_val = opts.get("min")
        max_val = opts.get("max")
        if min_val and value < min_val:
            return f"不能早于 {min_val}"
        if max_val and value > max_val:
            return f"不能晚于 {max_val}"

    # -- datetime -------------------------------------------------------
    elif ftype == "datetime":
        if not isinstance(value, str):
            return "必须是日期时间字符串"
        try:
            datetime.fromisoformat(value)
        except ValueError:
            return "日期时间格式不正确"

    # -- select ---------------------------------------------------------
    elif ftype == "select":
        if opts.get("api_endpoint"):
            # Dynamic select — choices come from API/DB, skip static validation
            pass
        else:
            choices = opts.get("choices", [])
            valid_values = [c["value"] for c in choices if "value" in c]
            if value not in valid_values:
                return f"必须在选项 {valid_values} 中选择"

    # -- relation -------------------------------------------------------
    elif ftype == "relation":
        if value is not None:
            target_id = value
            if not repo.exists(int(target_id)):
                return f"关联资产 {target_id} 不存在"

    # -- computed fields are read-only; silently skip validation ---------
    # (they should not appear in user-supplied custom_data)

    return None


def validate_custom_data(
    field_config: dict,
    custom_data: dict[str, Any] | None,
    repo: AssetRepo,
) -> dict[str, Any] | None:
    """Validate *custom_data* against *field_config* and return a cleaned copy.

    * Missing required fields → :class:`ValidationError`
    * Unknown field keys → silently dropped
    * Invalid values → :class:`ValidationError`
    """
    if custom_data is None:
        return None

    fields = field_config.get("fields", [])
    field_map: dict[str, dict] = {f["key"]: f for f in fields}

    errors: list[dict[str, str]] = []
    cleaned: dict[str, Any] = {}

    for key, fdef in field_map.items():
        # Skip computed fields (read-only)
        if fdef.get("type") == "computed":
            continue

        if key in custom_data:
            err = _validate_field(fdef, custom_data[key], repo)
            if err:
                errors.append({"field": key, "message": err})
            else:
                cleaned[key] = custom_data[key]
        elif fdef.get("required", False):
            errors.append({"field": key, "message": "该字段为必填项"})

    if errors:
        raise ValidationError(errors)

    return cleaned


# ---------------------------------------------------------------------------
# Computed fields
# ---------------------------------------------------------------------------

def evaluate_computed_fields(
    field_config: dict,
    custom_data: dict[str, Any] | None,
) -> dict[str, Any]:
    """Evaluate all *computed* fields and return ``{key: result}``.

    Missing dependency variables result in ``None`` rather than an error.
    """
    fields = field_config.get("fields", [])
    computed_fields = [f for f in fields if f.get("type") == "computed"]

    if not computed_fields:
        return {}

    data = custom_data or {}
    engine = ExpressionEngine()
    results: dict[str, Any] = {}

    for f in computed_fields:
        expr = (f.get("options") or {}).get("expression", "")
        if not expr:
            results[f["key"]] = None
            continue
        try:
            results[f["key"]] = engine.evaluate(expr, data)
        except (ExpressionError, Exception):
            results[f["key"]] = None

    return results


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class AssetService:
    """Business logic for the unified asset API."""

    def __init__(self, repo: AssetRepo, audit: AuditRepo):
        self.repo = repo
        self.audit = audit

    # ---- helpers -------------------------------------------------------

    def _enrich_item(self, item: dict) -> dict:
        """Transform flat DB fields into nested objects expected by the frontend.

        The repository returns flat columns (type_name, type_icon, category_name,
        type_field_config).  The frontend Asset TypeScript interface expects
        nested asset_type and category objects.  This method bridges that gap.
        """
        import json as _json

        # ---- Extract flat fields from DB row ----------------------------
        type_name = item.pop("type_name", "") or ""
        type_icon = item.pop("type_icon", "") or ""
        category_name = item.pop("category_name", "") or ""
        field_config_raw = item.pop("type_field_config", None)

        # ---- Parse field_config JSON ------------------------------------
        if isinstance(field_config_raw, str):
            try:
                field_config = _json.loads(field_config_raw)
            except (_json.JSONDecodeError, TypeError):
                field_config = {}
        elif isinstance(field_config_raw, dict):
            field_config = field_config_raw
        else:
            field_config = {}

        # ---- Build nested asset_type object -----------------------------
        item["asset_type"] = {
            "id": item.get("type_id"),
            "name": type_name,
            "icon": type_icon,
        }

        # ---- Build nested category object --------------------------------
        cat_id = item.get("category_id")
        if cat_id:
            item["category"] = {
                "id": cat_id,
                "name": category_name,
            }
        else:
            item["category"] = None

        # ---- Evaluate computed fields ------------------------------------
        item["computed_fields"] = evaluate_computed_fields(
            field_config, item.get("custom_data")
        )

        # ---- Derive a default status for display purposes ----------------
        # The unified assets table has no top-level status column.
        # For subscription-type assets the status lives inside custom_data.
        # For other types we default to "active" so the UI can display
        # something meaningful instead of "-".
        if "status" not in item or item["status"] is None:
            cd = item.get("custom_data") or {}
            item["status"] = cd.get("status", "active")

        return item

    def _validate_and_clean(
        self, type_id: int, custom_data: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        """Load field_config for *type_id* and validate *custom_data*."""
        asset_type = self.repo.get_type(type_id)
        if asset_type is None:
            raise ValueError("资产类型不存在")
        return validate_custom_data(
            asset_type.get("field_config", {}), custom_data, self.repo
        )

    # ---- public API ----------------------------------------------------

    def list(
        self,
        type_ids: list[int] | None = None,
        category_id: int | None = None,
        search: str = "",
        status: str = "",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        items, total = self.repo.list(
            type_ids=type_ids,
            category_id=category_id,
            search=search,
            status=status,
            page=page,
            page_size=page_size,
        )
        items = [self._enrich_item(it) for it in items]
        return items, total

    def get_by_id(self, id: int) -> dict:
        item = self.repo.get_by_id(id)
        return self._enrich_item(item)

    def create(
        self,
        type_id: int,
        name: str,
        category_id: int | None = None,
        custom_data: dict[str, Any] | None = None,
    ) -> dict:
        # Validate type exists + custom_data
        cleaned = self._validate_and_clean(type_id, custom_data)

        # Auto-set reminder_days for subscriptions if not provided
        if type_id == 3:
            if cleaned is None:
                cleaned = {}
            if "reminder_days" not in cleaned or cleaned["reminder_days"] is None:
                cleaned["reminder_days"] = self._calc_default_reminder_days(cleaned)

        asset = self.repo.create(
            type_id=type_id,
            name=name,
            category_id=category_id,
            custom_data=cleaned,
        )
        self.audit.log("asset", asset["id"], "create", {
            "name": name, "type_id": type_id,
        })
        return self._enrich_item(asset)

    def _calc_default_reminder_days(self, custom_data: dict) -> int:
        """Calculate default reminder_days based on subscription cycle."""
        cycle = custom_data.get("cycle")
        if not cycle:
            return 3
        try:
            period_id = int(cycle)
        except (ValueError, TypeError):
            return 3

        period = self.repo.db.execute(
            "SELECT * FROM subscription_periods WHERE id = ?", (period_id,)
        ).fetchone()
        if not period:
            return 3

        period = dict(period)
        rule_type = period.get("rule_type", "")

        if rule_type == "daily_interval":
            interval = period.get("interval_days", 0)
            hours = period.get("interval_hours", 0)
            cycle_days = interval + (hours / 24.0)
        elif rule_type == "monthly_day":
            cycle_days = 30
        elif rule_type == "yearly_date":
            cycle_days = 365
        elif rule_type == "custom":
            interval = period.get("interval_days", 0)
            hours = period.get("interval_hours", 0)
            cycle_days = interval + (hours / 24.0)
        else:
            cycle_days = 30  # fallback

        if cycle_days <= 0:
            return 3
        return min(3, int(cycle_days))

    def update(
        self,
        id: int,
        name: str | None = None,
        category_id: int | None = None,
        custom_data: dict[str, Any] | None = None,
    ) -> dict:
        # Ensure asset exists
        existing = self.repo.get_by_id(id)

        # Validate custom_data against the *existing* type
        cleaned = None
        if custom_data is not None:
            cleaned = self._validate_and_clean(existing["type_id"], custom_data)

        self.repo.update(id, name=name, category_id=category_id, custom_data=cleaned)
        self.audit.log("asset", id, "update", {
            "name": name, "category_id": category_id,
        })
        return self.get_by_id(id)

    def delete(self, id: int) -> None:
        # Raises ValueError if not found
        self.repo.get_by_id(id)
        self.repo.delete(id)
        self.audit.log("asset", id, "delete")

    def batch_delete(self, ids: list[int]) -> int:
        deleted = 0
        for aid in ids:
            try:
                self.delete(aid)
                deleted += 1
            except ValueError:
                pass
        return deleted
