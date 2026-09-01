from __future__ import annotations

import json
import sqlite3


class AuditRepo:
    """Audit log repository.

    SQL injection audit: All queries use parameterised placeholders (?).
    Dynamic WHERE clauses are built from a controlled list of fixed strings
    joined with AND — no user-supplied column names or raw SQL fragments.
    """
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def log(self, entity_type: str, entity_id: int, action: str,
            changed_fields: dict | None = None):
        fields_json = json.dumps(changed_fields or {})
        self.db.execute(
            "INSERT INTO audit_log (entity_type, entity_id, action, changed_fields) VALUES (?, ?, ?, ?)",
            (entity_type, entity_id, action, fields_json),
        )

    def list(self, entity_type: str = "", action: str = "",
             page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
        where_clauses = ["1=1"]
        args = []
        if entity_type:
            where_clauses.append("entity_type = ?")
            args.append(entity_type)
        if action:
            where_clauses.append("action = ?")
            args.append(action)

        where = " AND ".join(where_clauses)

        total = self.db.execute(
            f"SELECT COUNT(*) FROM audit_log WHERE {where}", args
        ).fetchone()[0]

        offset = (page - 1) * page_size
        rows = self.db.execute(
            f"SELECT * FROM audit_log WHERE {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            args + [page_size, offset],
        ).fetchall()
        return [dict(r) for r in rows], total
