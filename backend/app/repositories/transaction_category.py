from __future__ import annotations

import sqlite3


class TransactionCategoryRepo:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def create(self, name: str, icon: str, type: str,
               parent_id: int | None, sort_order: int) -> dict:
        cur = self.db.execute(
            """INSERT INTO transaction_categories
               (name, icon, type, parent_id, sort_order)
               VALUES (?, ?, ?, ?, ?)""",
            (name, icon, type, parent_id, sort_order),
        )
        return self.get_by_id(cur.lastrowid)

    def get_by_id(self, id: int) -> dict:
        row = self.db.execute(
            "SELECT * FROM transaction_categories WHERE id = ?", (id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"TransactionCategory {id} not found")
        return dict(row)

    def update(self, id: int, **fields) -> None:
        allowed = {"name", "icon", "sort_order"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [id]
        self.db.execute(
            f"UPDATE transaction_categories SET {set_clause} WHERE id = ?", values,
        )

    def delete(self, id: int) -> None:
        self.db.execute("DELETE FROM transaction_categories WHERE id = ?", (id,))

    def list_all(self) -> list[dict]:
        rows = self.db.execute(
            "SELECT * FROM transaction_categories ORDER BY sort_order, id"
        ).fetchall()
        return [dict(r) for r in rows]

    def list_by_type(self, type: str) -> list[dict]:
        rows = self.db.execute(
            "SELECT * FROM transaction_categories WHERE type = ? ORDER BY sort_order, id",
            (type,),
        ).fetchall()
        return [dict(r) for r in rows]

    def find_by_name(self, name: str, type: str) -> dict | None:
        row = self.db.execute(
            "SELECT * FROM transaction_categories WHERE name = ? AND type = ?",
            (name, type),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
