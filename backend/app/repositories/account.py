from __future__ import annotations

import sqlite3


class AccountRepo:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def create(self, name: str, type: str, balance: float, icon: str,
               notes: str, sort_order: int) -> dict:
        cur = self.db.execute(
            """INSERT INTO accounts (name, type, balance, icon, notes, sort_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, type, balance, icon, notes, sort_order),
        )
        return self.get_by_id(cur.lastrowid)

    def get_by_id(self, id: int) -> dict:
        row = self.db.execute(
            "SELECT * FROM accounts WHERE id = ?", (id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Account {id} not found")
        return dict(row)

    def update(self, id: int, **fields) -> None:
        allowed = {"name", "type", "balance", "icon", "notes", "sort_order", "is_active"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        # Convert bool to int for is_active
        if "is_active" in updates:
            updates["is_active"] = 1 if updates["is_active"] else 0
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [id]
        self.db.execute(
            f"UPDATE accounts SET {set_clause} WHERE id = ?", values,
        )

    def delete(self, id: int) -> None:
        self.db.execute("DELETE FROM accounts WHERE id = ?", (id,))

    def list_all(self, active_only: bool = False) -> list[dict]:
        if active_only:
            rows = self.db.execute(
                "SELECT * FROM accounts WHERE is_active = 1 ORDER BY sort_order, id"
            ).fetchall()
        else:
            rows = self.db.execute(
                "SELECT * FROM accounts ORDER BY sort_order, id"
            ).fetchall()
        return [dict(r) for r in rows]

    def update_balance(self, id: int, delta: float) -> None:
        self.db.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (delta, id),
        )
