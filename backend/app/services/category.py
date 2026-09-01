"""Category service — unified category management scoped by asset type."""

from __future__ import annotations

from backend.app.repositories.category import CategoryRepo
from backend.app.repositories.audit import AuditRepo


class CategoryService:
    """Business logic for unified categories (scoped by type_id)."""

    def __init__(self, repo: CategoryRepo, audit: AuditRepo):
        self.repo = repo
        self.audit = audit

    def list_tree(self, type_id: int) -> list[dict]:
        self.repo.verify_type_exists(type_id)
        return self.repo.list_tree(type_id)

    def get_by_id(self, id: int) -> dict:
        return self.repo.get_by_id(id)

    def create(
        self,
        type_id: int,
        name: str,
        parent_id: int | None = None,
        icon: str = "",
        sort_order: int = 0,
    ) -> dict:
        self.repo.verify_type_exists(type_id)
        cat = self.repo.create(type_id, name, parent_id, icon, sort_order)
        self.audit.log(
            "category", cat["id"], "create",
            {"type_id": type_id, "name": name},
        )
        return cat

    def update(
        self,
        id: int,
        *,
        name: str | None = None,
        icon: str | None = None,
        sort_order: int | None = None,
        parent_id: int | None = None,
    ) -> dict:
        cat = self.repo.update(
            id, name=name, icon=icon, sort_order=sort_order, parent_id=parent_id,
        )
        self.audit.log("category", id, "update", {"name": name})
        return cat

    def delete(self, id: int) -> None:
        self.repo.delete(id)
        self.audit.log("category", id, "delete")
