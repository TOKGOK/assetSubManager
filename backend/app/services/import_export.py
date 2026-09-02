from __future__ import annotations

import csv
import io
import json

from backend.app.repositories.asset import AssetRepo
from backend.app.repositories.category import CategoryRepo
from backend.app.repositories.audit import AuditRepo


# Physical asset type ID (defined in database.py)
TYPE_PHYSICAL = 1


class ImportExportService:
    def __init__(self, asset_repo: AssetRepo, category_repo: CategoryRepo, audit_repo: AuditRepo):
        self.asset_repo = asset_repo
        self.category_repo = category_repo
        self.audit_repo = audit_repo

    # ── Export ────────────────────────────────────────────────

    def _extract_physical(self, a: dict) -> dict:
        """Extract physical-asset fields from a unified asset dict."""
        cd = a.get("custom_data") or {}
        if isinstance(cd, str):
            try:
                cd = json.loads(cd)
            except (json.JSONDecodeError, TypeError):
                cd = {}
        return {
            "name": a.get("name", ""),
            "category_name": a.get("category_name", ""),
            "purchase_date": cd.get("purchase_date", ""),
            "value": cd.get("value", 0),
            "currency": cd.get("currency", "CNY"),
            "notes": cd.get("notes", ""),
            "custom_fields": {
                k: v for k, v in cd.items()
                if k not in {"purchase_date", "value", "currency", "notes"}
            },
        }

    def export_csv(self) -> str:
        assets = self.asset_repo.list_all()
        physical = [self._extract_physical(a) for a in assets if a.get("type_id") == TYPE_PHYSICAL]
        # Collect all custom field names across all assets
        field_names: list[str] = []
        seen: set[str] = set()
        for a in physical:
            for fn in a["custom_fields"]:
                if fn not in seen:
                    seen.add(fn)
                    field_names.append(fn)

        output = io.StringIO()
        writer = csv.writer(output)
        header = [
            "name", "category", "purchase_date", "value",
            "currency", "notes",
        ] + field_names
        writer.writerow(header)

        for a in physical:
            row = [
                a["name"],
                a["category_name"],
                a["purchase_date"],
                a["value"],
                a["currency"],
                a["notes"],
            ] + [a["custom_fields"].get(fn, "") for fn in field_names]
            writer.writerow(row)

        self.audit_repo.log("system", 0, "export", {"format": "csv"})
        return output.getvalue()

    def export_json(self) -> str:
        assets = self.asset_repo.list_all()
        result = []
        for a in assets:
            if a.get("type_id") != TYPE_PHYSICAL:
                continue
            p = self._extract_physical(a)
            result.append({
                "name": p["name"],
                "category_name": p["category_name"],
                "purchase_date": p["purchase_date"],
                "value": p["value"],
                "currency": p["currency"],
                "notes": p["notes"],
                "custom_fields": p["custom_fields"],
            })

        self.audit_repo.log("system", 0, "export", {"format": "json"})
        return json.dumps(result, ensure_ascii=False, indent=2)

    def export_sql(self) -> str:
        lines = []
        for line in self.asset_repo.db.iterdump():
            lines.append(line)
        self.audit_repo.log("system", 0, "export", {"format": "sql"})
        return "\n".join(lines)

    # ── Import ────────────────────────────────────────────────

    def import_csv(self, content: str) -> dict:
        reader = csv.DictReader(io.StringIO(content))
        created = 0
        skipped = 0
        errors: list[dict] = []

        for idx, row in enumerate(reader, start=1):
            try:
                name = row.get("name", "").strip()
                category_name = row.get("category", "").strip()
                if not name:
                    errors.append({"row": idx, "error": "empty name"})
                    continue
                if not category_name:
                    errors.append({"row": idx, "error": "empty category"})
                    continue

                # Find or create category (type_id=1 for physical assets)
                cat = self.category_repo.find_by_name(category_name, type_id=TYPE_PHYSICAL)
                if cat is None:
                    cat = self.category_repo.create_simple(category_name, type_id=TYPE_PHYSICAL)
                category_id = cat["id"]

                # Dedup check
                existing = self.asset_repo.db.execute(
                    "SELECT id FROM assets WHERE name = ? AND category_id = ? AND type_id = ?",
                    (name, category_id, TYPE_PHYSICAL),
                ).fetchone()
                if existing:
                    skipped += 1
                    continue

                # Build custom_data from CSV columns
                custom_data: dict = {}
                # Backward compat: old CSV may use "purchase_price"
                if "purchase_price" in row and "value" not in row:
                    row["value"] = row.pop("purchase_price")
                for col in ("purchase_date", "value", "currency", "notes"):
                    val = row.get(col, "")
                    if val:
                        if col == "value":
                            custom_data[col] = _float(val)
                        else:
                            custom_data[col] = val

                # Extra columns become custom fields
                base_cols = {"name", "category", "purchase_date", "value",
                             "currency", "notes"}
                for k, v in row.items():
                    if k and k not in base_cols and v:
                        custom_data[k] = v

                self.asset_repo.create(
                    type_id=TYPE_PHYSICAL,
                    name=name,
                    category_id=category_id,
                    custom_data=custom_data,
                )
                created += 1
            except Exception as e:
                errors.append({"row": idx, "error": str(e)})

        self.audit_repo.log("system", 0, "import", {
            "format": "csv", "created": created, "skipped": skipped, "errors": len(errors),
        })
        return {"created": created, "skipped": skipped, "errors": errors}

    def import_sql(self, content: str) -> dict:
        """从 SQL dump 恢复数据库。使用 executescript 执行。"""
        try:
            self.asset_repo.db.executescript(content)
            self.audit_repo.log("system", 0, "import", {"format": "sql"})
            return {"success": True, "errors": []}
        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    def import_json(self, content: str) -> dict:
        try:
            items = json.loads(content)
        except json.JSONDecodeError as e:
            return {"created": 0, "skipped": 0, "errors": [{"row": 0, "error": f"invalid JSON: {e}"}]}

        if not isinstance(items, list):
            return {"created": 0, "skipped": 0, "errors": [{"row": 0, "error": "expected JSON array"}]}

        created = 0
        skipped = 0
        errors: list[dict] = []

        for idx, item in enumerate(items, start=1):
            try:
                name = str(item.get("name", "")).strip()
                category_name = str(item.get("category_name", "")).strip()
                if not name:
                    errors.append({"row": idx, "error": "empty name"})
                    continue
                if not category_name:
                    errors.append({"row": idx, "error": "empty category_name"})
                    continue

                cat = self.category_repo.find_by_name(category_name, type_id=TYPE_PHYSICAL)
                if cat is None:
                    cat = self.category_repo.create_simple(category_name, type_id=TYPE_PHYSICAL)
                category_id = cat["id"]

                existing = self.asset_repo.db.execute(
                    "SELECT id FROM assets WHERE name = ? AND category_id = ? AND type_id = ?",
                    (name, category_id, TYPE_PHYSICAL),
                ).fetchone()
                if existing:
                    skipped += 1
                    continue

                # Build custom_data from JSON item
                custom_data: dict = {}
                # Backward compat: old JSON may use "purchase_price"
                if item.get("purchase_price") is not None and item.get("value") is None:
                    item["value"] = item.pop("purchase_price")
                for key in ("purchase_date", "value", "currency", "notes"):
                    val = item.get(key)
                    if val is not None:
                        custom_data[key] = val
                # Merge any extra custom_fields
                extra = item.get("custom_fields", {})
                if isinstance(extra, dict):
                    custom_data.update({k: str(v) for k, v in extra.items()})

                self.asset_repo.create(
                    type_id=TYPE_PHYSICAL,
                    name=name,
                    category_id=category_id,
                    custom_data=custom_data or None,
                )
                created += 1
            except Exception as e:
                errors.append({"row": idx, "error": str(e)})

        self.audit_repo.log("system", 0, "import", {
            "format": "json", "created": created, "skipped": skipped, "errors": len(errors),
        })
        return {"created": created, "skipped": skipped, "errors": errors}


def _float(val: str | None) -> float:
    try:
        return float(val or 0)
    except (ValueError, TypeError):
        return 0
