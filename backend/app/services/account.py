from __future__ import annotations

from backend.app.repositories.account import AccountRepo
from backend.app.repositories.audit import AuditRepo
from backend.app.models.transaction import UpdateAccountRequest


class AccountService:
    def __init__(self, repo: AccountRepo, audit: AuditRepo):
        self.repo = repo
        self.audit = audit

    def create(self, name: str, type: str, balance: float = 0,
               icon: str = "", notes: str = "", sort_order: int = 0) -> dict:
        try:
            account = self.repo.create(name, type, balance, icon, notes, sort_order)
            self.audit.log("account", account["id"], "create", {"name": name, "type": type})
            self.repo.db.commit()
            return account
        except Exception:
            self.repo.db.rollback()
            raise

    def get_by_id(self, id: int) -> dict:
        return self.repo.get_by_id(id)

    def update(self, id: int, req: UpdateAccountRequest) -> None:
        update_data = req.model_dump(exclude_unset=True)
        try:
            self.repo.update(id, **update_data)
            self.audit.log("account", id, "update", update_data)
            self.repo.db.commit()
        except Exception:
            self.repo.db.rollback()
            raise

    def delete(self, id: int) -> None:
        try:
            self.repo.delete(id)
            self.audit.log("account", id, "delete")
            self.repo.db.commit()
        except Exception:
            self.repo.db.rollback()
            raise

    def list_all(self, active_only: bool = False) -> list[dict]:
        return self.repo.list_all(active_only=active_only)
