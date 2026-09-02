"""Unified asset repository.

Provides CRUD operations on the ``assets`` table (the new unified table that
replaces the legacy per-type tables).  Uses raw ``sqlite3`` to stay consistent
with the existing repository layer.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any


class AssetRepo:
    """Unified asset CRUD repository backed by the ``assets`` table."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        """Convert a sqlite3.Row into a plain dict, parsing JSON fields."""
        d = dict(row)
        # custom_data may come back as a JSON string from SQLite
        if "custom_data" in d and isinstance(d["custom_data"], str):
            try:
                d["custom_data"] = json.loads(d["custom_data"])
            except (json.JSONDecodeError, TypeError):
                d["custom_data"] = d["custom_data"] or None
        return d

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(
        self,
        type_id: int,
        name: str,
        category_id: int | None = None,
        custom_data: dict[str, Any] | None = None,
    ) -> dict:
        """Insert a new asset and return the full row (joined with type/category)."""
        custom_json = json.dumps(custom_data) if custom_data else None
        cur = self.db.execute(
            "INSERT INTO assets (type_id, category_id, name, custom_data) "
            "VALUES (?, ?, ?, ?)",
            (type_id, category_id, name, custom_json),
        )
        self.db.commit()
        return self.get_by_id(cur.lastrowid)

    def get_by_id(self, id: int) -> dict:
        """Return a single asset with joined type / category names.

        Raises ``ValueError`` if the asset does not exist.
        """
        row = self.db.execute(
            """SELECT a.id, a.type_id, a.category_id, a.name, a.custom_data,
                      a.created_at, a.updated_at,
                      COALESCE(t.name, '')  AS type_name,
                      COALESCE(t.icon, '')  AS type_icon,
                      COALESCE(t.field_config, '{}') AS type_field_config,
                      COALESCE(c.name, '')  AS category_name
               FROM assets a
               JOIN asset_types t ON a.type_id = t.id
               LEFT JOIN categories c ON a.category_id = c.id
               WHERE a.id = ?""",
            (id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Asset {id} not found")
        return self._row_to_dict(row)

    def update(
        self,
        id: int,
        name: str | None = None,
        category_id: int | None = None,
        custom_data: dict[str, Any] | None = None,
    ) -> None:
        """Update an asset.  Only non-None fields are written."""
        sets: list[str] = ["updated_at = datetime('now')"]
        args: list[Any] = []

        if name is not None:
            sets.append("name = ?")
            args.append(name)
        if category_id is not None:
            sets.append("category_id = ?")
            args.append(category_id)
        if custom_data is not None:
            sets.append("custom_data = ?")
            args.append(json.dumps(custom_data))

        args.append(id)
        self.db.execute(
            f"UPDATE assets SET {', '.join(sets)} WHERE id = ?", args
        )
        self.db.commit()

    def delete(self, id: int) -> None:
        self.db.execute("DELETE FROM assets WHERE id = ?", (id,))
        self.db.commit()

    def batch_delete(self, ids: list[int]) -> int:
        """Delete multiple assets.  Returns the number actually deleted."""
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        cur = self.db.execute(
            f"DELETE FROM assets WHERE id IN ({placeholders})", ids
        )
        self.db.commit()
        return cur.rowcount

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def exists(self, id: int) -> bool:
        row = self.db.execute(
            "SELECT 1 FROM assets WHERE id = ?", (id,)
        ).fetchone()
        return row is not None

    def list(
        self,
        type_ids: list[int] | None = None,
        category_id: int | None = None,
        search: str = "",
        status: str = "",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """Return a paginated list of assets with optional filters.

        *search* matches against ``name`` and stringified ``custom_data``.
        *status* filters by the status value inside custom_data.
        """
        where_clauses: list[str] = ["1=1"]
        args: list[Any] = []

        if type_ids:
            placeholders = ",".join("?" for _ in type_ids)
            where_clauses.append(f"a.type_id IN ({placeholders})")
            args.extend(type_ids)

        if category_id is not None:
            where_clauses.append("a.category_id = ?")
            args.append(category_id)

        if search:
            where_clauses.append(
                "(a.name LIKE ? OR CAST(a.custom_data AS TEXT) LIKE ?)"
            )
            args.extend([f"%{search}%", f"%{search}%"])

        if status:
            if status == "active":
                # "active" includes rows where status is missing/null
                # (the service layer defaults those to "active")
                where_clauses.append(
                    "(COALESCE(json_extract(a.custom_data, '$.status'), 'active') = ?)"
                )
            else:
                where_clauses.append(
                    "(json_extract(a.custom_data, '$.status') = ?)"
                )
            args.append(status)

        where = " AND ".join(where_clauses)

        total: int = self.db.execute(
            f"SELECT COUNT(*) FROM assets a WHERE {where}", args
        ).fetchone()[0]

        offset = (page - 1) * page_size
        rows = self.db.execute(
            f"""SELECT a.id, a.type_id, a.category_id, a.name, a.custom_data,
                       a.created_at, a.updated_at,
                       COALESCE(t.name, '')  AS type_name,
                       COALESCE(t.icon, '')  AS type_icon,
                       COALESCE(t.field_config, '{{}}') AS type_field_config,
                       COALESCE(c.name, '')  AS category_name
                FROM assets a
                JOIN asset_types t ON a.type_id = t.id
                LEFT JOIN categories c ON a.category_id = c.id
                WHERE {where}
                ORDER BY a.id DESC
                LIMIT ? OFFSET ?""",
            args + [page_size, offset],
        ).fetchall()

        items = [self._row_to_dict(r) for r in rows]
        return items, total

    # ------------------------------------------------------------------
    # Type helpers (used by service layer)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Stats helpers (used by dashboard / import-export)
    # ------------------------------------------------------------------

    def count_by_type(self, type_id: int) -> int:
        """Count assets of a given type."""
        row = self.db.execute(
            "SELECT COUNT(*) FROM assets WHERE type_id = ?", (type_id,)
        ).fetchone()
        return row[0] if row else 0

    def sum_custom_field(self, type_id: int, field_key: str) -> float:
        """Sum a numeric custom_data field across all assets of a type."""
        row = self.db.execute(
            "SELECT COALESCE(SUM(CAST(json_extract(custom_data, ?) AS REAL)), 0) "
            "FROM assets WHERE type_id = ?",
            (f"$.{field_key}", type_id),
        ).fetchone()
        return float(row[0]) if row else 0.0

    def status_counts_by_type(self, type_id: int) -> dict[str, int]:
        """Count assets grouped by custom_data->status for a given type."""
        rows = self.db.execute(
            "SELECT COALESCE(json_extract(custom_data, '$.status'), 'unknown') AS s, "
            "COUNT(*) AS cnt FROM assets WHERE type_id = ? GROUP BY s",
            (type_id,),
        ).fetchall()
        return {r[0]: r[1] for r in rows}

    def list_by_type(self, type_id: int) -> list[dict]:
        """Return all assets of a given type (with parsed custom_data)."""
        rows = self.db.execute(
            """SELECT a.id, a.type_id, a.category_id, a.name, a.custom_data,
                      a.created_at, a.updated_at,
                      COALESCE(t.name, '')  AS type_name,
                      COALESCE(t.icon, '')  AS type_icon,
                      COALESCE(t.field_config, '{}') AS type_field_config,
                      COALESCE(c.name, '')  AS category_name
               FROM assets a
               JOIN asset_types t ON a.type_id = t.id
               LEFT JOIN categories c ON a.category_id = c.id
               WHERE a.type_id = ?
               ORDER BY a.id DESC""",
            (type_id,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def upcoming_renewals(self, type_id: int, days: int = 30) -> list[dict]:
        """Return subscription assets with next_renewal within *days*."""
        from datetime import datetime, timedelta
        today = datetime.now().strftime("%Y-%m-%d")
        future = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        rows = self.db.execute(
            """SELECT a.id, a.type_id, a.category_id, a.name, a.custom_data,
                      a.created_at, a.updated_at,
                      COALESCE(t.name, '')  AS type_name,
                      COALESCE(t.icon, '')  AS type_icon,
                      COALESCE(t.field_config, '{}') AS type_field_config,
                      COALESCE(c.name, '')  AS category_name
               FROM assets a
               JOIN asset_types t ON a.type_id = t.id
               LEFT JOIN categories c ON a.category_id = c.id
               WHERE a.type_id = ?
                 AND json_extract(a.custom_data, '$.next_renewal') >= ?
                 AND json_extract(a.custom_data, '$.next_renewal') <= ?
                 AND COALESCE(json_extract(a.custom_data, '$.status'), '') = 'active'
               ORDER BY json_extract(a.custom_data, '$.next_renewal') ASC""",
            (type_id, today, future),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def monthly_subscription_total(self, type_id: int) -> float:
        """Sum the monthly-equivalent amount for active subscription assets."""
        rows = self.db.execute(
            """SELECT custom_data FROM assets
               WHERE type_id = ?
                 AND COALESCE(json_extract(custom_data, '$.status'), '') = 'active'""",
            (type_id,),
        ).fetchall()
        total = 0.0
        for row in rows:
            d = dict(row)
            cd = d.get("custom_data")
            if isinstance(cd, str):
                try:
                    cd = json.loads(cd)
                except (json.JSONDecodeError, TypeError):
                    cd = {}
            if not isinstance(cd, dict):
                continue
            amount = float(cd.get("value", 0) or 0)
            cycle = str(cd.get("cycle", "") or "")
            # Convert cycle to monthly
            if cycle == "monthly" or cycle == "月付":
                total += amount
            elif cycle == "quarterly" or cycle == "季付":
                total += amount / 3
            elif cycle == "yearly" or cycle == "年付":
                total += amount / 12
            else:
                total += amount  # default: treat as monthly
        return total

    def list_all(self) -> list[dict]:
        """Return all assets (with parsed custom_data and joined names)."""
        rows = self.db.execute(
            """SELECT a.id, a.type_id, a.category_id, a.name, a.custom_data,
                      a.created_at, a.updated_at,
                      COALESCE(t.name, '')  AS type_name,
                      COALESCE(t.icon, '')  AS type_icon,
                      COALESCE(t.field_config, '{}') AS type_field_config,
                      COALESCE(c.name, '')  AS category_name
               FROM assets a
               JOIN asset_types t ON a.type_id = t.id
               LEFT JOIN categories c ON a.category_id = c.id
               ORDER BY a.id DESC"""
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_type(self, type_id: int) -> dict | None:
        """Return an asset_types row as a dict, or *None*."""
        row = self.db.execute(
            "SELECT * FROM asset_types WHERE id = ?", (type_id,)
        ).fetchone()
        if row is None:
            return None
        d = dict(row)
        if isinstance(d.get("field_config"), str):
            try:
                d["field_config"] = json.loads(d["field_config"])
            except (json.JSONDecodeError, TypeError):
                d["field_config"] = {}
        return d
