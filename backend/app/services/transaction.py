from __future__ import annotations

from backend.app.repositories.transaction import TransactionRepo
from backend.app.repositories.account import AccountRepo
from backend.app.repositories.audit import AuditRepo
from backend.app.models.transaction import UpdateTransactionRequest
from backend.app.services.bill_parser import ParsedTransaction


class TransactionService:
    def __init__(self, repo: TransactionRepo, account_repo: AccountRepo,
                 audit: AuditRepo):
        self.repo = repo
        self.account_repo = account_repo
        self.audit = audit

    def create(self, **kwargs) -> dict:
        try:
            txn = self.repo.create(**kwargs)
            self._apply_balance(txn)
            self.repo.db.commit()
            self.audit.log("transaction", txn["id"], "create",
                           {"type": txn["type"], "amount": txn["amount"]})
            self.repo.db.commit()
            return txn
        except Exception:
            self.repo.db.rollback()
            raise

    def update(self, id: int, req: UpdateTransactionRequest) -> dict:
        update_data = req.model_dump(exclude_unset=True)
        try:
            old_txn = self.repo.get_by_id(id)
            # Roll back old balance effects
            self._reverse_balance(old_txn)
            # Apply updates
            self.repo.update(id, **update_data)
            new_txn = self.repo.get_by_id(id)
            # Apply new balance effects
            self._apply_balance(new_txn)
            self.repo.db.commit()
            self.audit.log("transaction", id, "update", update_data)
            self.repo.db.commit()
            return new_txn
        except Exception:
            self.repo.db.rollback()
            raise

    def delete(self, id: int) -> None:
        try:
            txn = self.repo.get_by_id(id)
            self._reverse_balance(txn)
            self.repo.delete(id)
            self.repo.db.commit()
            self.audit.log("transaction", id, "delete")
            self.repo.db.commit()
        except Exception:
            self.repo.db.rollback()
            raise

    def get_by_id(self, id: int) -> dict:
        return self.repo.get_by_id(id)

    def list(self, **filters) -> tuple[list[dict], int]:
        return self.repo.list(**filters)

    def batch_delete(self, ids: list[int]) -> int:
        deleted_ids = []
        try:
            for txn_id in ids:
                try:
                    txn = self.repo.get_by_id(txn_id)
                except ValueError:
                    continue
                self._reverse_balance(txn)
                self.repo.delete(txn_id)
                deleted_ids.append(txn_id)
            self.repo.db.commit()
        except Exception:
            self.repo.db.rollback()
            raise
        # Audit logs after successful commit
        for txn_id in deleted_ids:
            self.audit.log("transaction", txn_id, "delete")
        self.repo.db.commit()
        return len(deleted_ids)

    def get_stats(self, date_from: str = "", date_to: str = "") -> dict:
        return self.repo.get_stats(date_from, date_to)

    def import_transactions(self, parsed_txns: list[ParsedTransaction],
                           source: str, default_account_id: int | None = None) -> dict:
        """批量导入交易记录（不更新账户余额）

        Returns:
            {"created": int, "skipped": int, "errors": list[str]}
        """
        created = 0
        skipped = 0
        errors = []

        try:
            for i, txn in enumerate(parsed_txns):
                # 去重检查
                existing = self.repo.find_by_source_and_original_id(source, txn.original_id)
                if existing:
                    skipped += 1
                    continue

                self.repo.create(
                    type=txn.type,
                    amount=txn.amount,
                    category_id=None,
                    account_id=default_account_id,
                    to_account_id=None,
                    transaction_date=txn.transaction_date,
                    merchant=txn.merchant,
                    note=txn.note,
                    source=source,
                    original_id=txn.original_id,
                )
                created += 1
            self.repo.db.commit()
        except Exception as e:
            self.repo.db.rollback()
            errors.append(f"导入失败: {str(e)}")
            return {"created": 0, "skipped": skipped, "errors": errors}

        return {"created": created, "skipped": skipped, "errors": errors}

    # ---- balance helpers ----

    def _apply_balance(self, txn: dict) -> None:
        """Apply transaction's effect on account balances."""
        txn_type = txn["type"]
        amount = txn["amount"]
        account_id = txn["account_id"]
        to_account_id = txn.get("to_account_id")

        if txn_type == "income" and account_id:
            self.account_repo.update_balance(account_id, amount)
        elif txn_type == "expense" and account_id:
            self.account_repo.update_balance(account_id, -amount)
        elif txn_type == "transfer":
            if account_id:
                self.account_repo.update_balance(account_id, -amount)
            if to_account_id:
                self.account_repo.update_balance(to_account_id, amount)

    def _reverse_balance(self, txn: dict) -> None:
        """Reverse transaction's effect on account balances."""
        txn_type = txn["type"]
        amount = txn["amount"]
        account_id = txn["account_id"]
        to_account_id = txn.get("to_account_id")

        if txn_type == "income" and account_id:
            self.account_repo.update_balance(account_id, -amount)
        elif txn_type == "expense" and account_id:
            self.account_repo.update_balance(account_id, amount)
        elif txn_type == "transfer":
            if account_id:
                self.account_repo.update_balance(account_id, amount)
            if to_account_id:
                self.account_repo.update_balance(to_account_id, -amount)
