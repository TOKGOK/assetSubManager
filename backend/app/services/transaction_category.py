from __future__ import annotations

from backend.app.repositories.transaction_category import TransactionCategoryRepo
from backend.app.repositories.audit import AuditRepo
from backend.app.models.transaction import UpdateTransactionCategoryRequest


class TransactionCategoryService:
    def __init__(self, repo: TransactionCategoryRepo, audit: AuditRepo):
        self.repo = repo
        self.audit = audit

    def create(self, name: str, icon: str = "", type: str = "expense",
               parent_id: int | None = None, sort_order: int = 0) -> dict:
        try:
            cat = self.repo.create(name, icon, type, parent_id, sort_order)
            self.audit.log("transaction_category", cat["id"], "create",
                           {"name": name, "type": type})
            self.repo.db.commit()
            return cat
        except Exception:
            self.repo.db.rollback()
            raise

    def get_by_id(self, id: int) -> dict:
        return self.repo.get_by_id(id)

    def update(self, id: int, req: UpdateTransactionCategoryRequest) -> None:
        update_data = req.model_dump(exclude_unset=True)
        try:
            self.repo.update(id, **update_data)
            self.audit.log("transaction_category", id, "update", update_data)
            self.repo.db.commit()
        except Exception:
            self.repo.db.rollback()
            raise

    def delete(self, id: int) -> None:
        try:
            self.repo.delete(id)
            self.audit.log("transaction_category", id, "delete")
            self.repo.db.commit()
        except Exception:
            self.repo.db.rollback()
            raise

    def list_all(self) -> list[dict]:
        return self.repo.list_all()

    def list_by_type(self, type: str) -> list[dict]:
        return self.repo.list_by_type(type)
