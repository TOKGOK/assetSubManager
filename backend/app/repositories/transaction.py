from __future__ import annotations

import sqlite3

# Whitelist of columns allowed for ORDER BY in list() to prevent SQL injection.
_ALLOWED_SORT_COLUMNS = {"transaction_date", "amount", "created_at"}


class TransactionRepo:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def create(self, type: str, amount: float, category_id: int | None,
               account_id: int | None, to_account_id: int | None,
               transaction_date: str, merchant: str, note: str,
               source: str = "manual", original_id: str = "") -> dict:
        cur = self.db.execute(
            """INSERT INTO transactions
               (type, amount, category_id, account_id, to_account_id,
                transaction_date, merchant, note, source, original_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (type, amount, category_id, account_id, to_account_id,
             transaction_date, merchant, note, source, original_id),
        )
        return self.get_by_id(cur.lastrowid)

    def get_by_id(self, id: int) -> dict:
        row = self.db.execute(
            """SELECT t.*,
                      COALESCE(tc.name, '') AS category_name,
                      COALESCE(tc.icon, '') AS category_icon,
                      COALESCE(a.name, '') AS account_name
               FROM transactions t
               LEFT JOIN transaction_categories tc ON t.category_id = tc.id
               LEFT JOIN accounts a ON t.account_id = a.id
               WHERE t.id = ?""",
            (id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"Transaction {id} not found")
        return dict(row)

    def update(self, id: int, **fields) -> None:
        allowed = {
            "type", "amount", "category_id", "account_id", "to_account_id",
            "transaction_date", "merchant", "note",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        updates["updated_at"] = "datetime('now')"
        set_parts = []
        values = []
        for k, v in updates.items():
            if v == "datetime('now')":
                set_parts.append(f"{k} = datetime('now')")
            else:
                set_parts.append(f"{k} = ?")
                values.append(v)
        values.append(id)
        set_clause = ", ".join(set_parts)
        self.db.execute(
            f"UPDATE transactions SET {set_clause} WHERE id = ?", values,
        )

    def delete(self, id: int) -> None:
        self.db.execute("DELETE FROM transactions WHERE id = ?", (id,))

    def list(self, type: str = "", category_id: int | None = None,
             account_id: int | None = None, date_from: str = "",
             date_to: str = "", search: str = "", sort_by: str = "",
             sort_order: str = "", page: int = 1,
             page_size: int = 20) -> tuple[list[dict], int]:
        where_clauses = ["1=1"]
        args: list = []

        if type:
            where_clauses.append("t.type = ?")
            args.append(type)
        if category_id is not None:
            where_clauses.append("t.category_id = ?")
            args.append(category_id)
        if account_id is not None:
            where_clauses.append("(t.account_id = ? OR t.to_account_id = ?)")
            args.extend([account_id, account_id])
        if date_from:
            where_clauses.append("t.transaction_date >= ?")
            args.append(date_from)
        if date_to:
            where_clauses.append("t.transaction_date <= ?")
            args.append(date_to)
        if search:
            where_clauses.append("(t.merchant LIKE ? OR t.note LIKE ?)")
            args.extend([f"%{search}%", f"%{search}%"])

        where = " AND ".join(where_clauses)

        total = self.db.execute(
            f"SELECT COUNT(*) FROM transactions t WHERE {where}", args,
        ).fetchone()[0]

        order = "t.transaction_date DESC, t.id DESC"
        if sort_by and sort_by in _ALLOWED_SORT_COLUMNS:
            direction = "DESC" if sort_order == "desc" else "ASC"
            order = f"t.{sort_by} {direction}"

        offset = (page - 1) * page_size
        rows = self.db.execute(
            f"""SELECT t.*,
                       COALESCE(tc.name, '') AS category_name,
                       COALESCE(tc.icon, '') AS category_icon,
                       COALESCE(a.name, '') AS account_name
                FROM transactions t
                LEFT JOIN transaction_categories tc ON t.category_id = tc.id
                LEFT JOIN accounts a ON t.account_id = a.id
                WHERE {where} ORDER BY {order} LIMIT ? OFFSET ?""",
            args + [page_size, offset],
        ).fetchall()

        return [dict(r) for r in rows], total

    def batch_delete(self, ids: list[int]) -> int:
        if not ids:
            return 0
        placeholders = ", ".join("?" for _ in ids)
        cur = self.db.execute(
            f"DELETE FROM transactions WHERE id IN ({placeholders})", ids,
        )
        return cur.rowcount

    def get_stats(self, date_from: str = "", date_to: str = "") -> dict:
        where_clauses = ["1=1"]
        args: list = []
        if date_from:
            where_clauses.append("transaction_date >= ?")
            args.append(date_from)
        if date_to:
            where_clauses.append("transaction_date <= ?")
            args.append(date_to)

        where = " AND ".join(where_clauses)

        row = self.db.execute(
            f"""SELECT
                    COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS total_income,
                    COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS total_expense,
                    COUNT(*) AS transaction_count
                FROM transactions
                WHERE {where}""",
            args,
        ).fetchone()
        stats = dict(row)
        stats["balance"] = stats["total_income"] - stats["total_expense"]

        # Category breakdown
        cat_rows = self.db.execute(
            f"""SELECT tc.id AS category_id,
                       COALESCE(tc.name, '未分类') AS category_name,
                       COALESCE(tc.icon, '') AS category_icon,
                       t.type,
                       COUNT(*) AS count,
                       SUM(t.amount) AS total_amount
                FROM transactions t
                LEFT JOIN transaction_categories tc ON t.category_id = tc.id
                WHERE {where.replace('1=1', '1=1')}
                GROUP BY tc.id, t.type
                ORDER BY total_amount DESC""",
            args,
        ).fetchall()
        stats["category_breakdown"] = [dict(r) for r in cat_rows]

        return stats

    def find_by_source_and_original_id(self, source: str, original_id: str) -> dict | None:
        row = self.db.execute(
            "SELECT * FROM transactions WHERE source = ? AND original_id = ?",
            (source, original_id),
        ).fetchone()
        if row is None:
            return None
        return dict(row)
