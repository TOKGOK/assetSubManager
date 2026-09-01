"""Category repository — unified categories with type_id.

Manages the ``categories`` table which now has a ``type_id`` foreign key
pointing to ``asset_types``, so each asset type maintains its own category
tree.

SQL injection audit: All queries use parameterised placeholders (?).
No string concatenation or f-strings in SQL statements.
"""

from __future__ import annotations

import sqlite3


class CategoryRepo:
    """Unified category repository (scoped by type_id)."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(
        self,
        type_id: int,
        name: str,
        parent_id: int | None = None,
        icon: str = "",
        sort_order: int = 0,
    ) -> dict:
        """Create a new category under *type_id*.

        If *parent_id* is given, validates that the parent exists and belongs
        to the same *type_id*.
        """
        if parent_id is not None:
            parent = self.db.execute(
                "SELECT id, type_id FROM categories WHERE id = ?", (parent_id,)
            ).fetchone()
            if parent is None:
                raise ValueError(f"Parent category {parent_id} does not exist")
            if parent["type_id"] != type_id:
                raise ValueError(
                    f"Parent category {parent_id} does not belong to type {type_id}"
                )

        cur = self.db.execute(
            "INSERT INTO categories (type_id, name, parent_id, icon, sort_order) "
            "VALUES (?, ?, ?, ?, ?)",
            (type_id, name, parent_id, icon, sort_order),
        )
        self.db.commit()
        return self.get_by_id(cur.lastrowid)

    def get_by_id(self, id: int) -> dict:
        row = self.db.execute(
            "SELECT * FROM categories WHERE id = ?", (id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Category {id} not found")
        return dict(row)

    def list_tree(self, type_id: int) -> list[dict]:
        """Return the full category tree for *type_id*."""
        rows = self.db.execute(
            "SELECT * FROM categories WHERE type_id = ? ORDER BY sort_order, id",
            (type_id,),
        ).fetchall()
        all_cats = [dict(r) for r in rows]
        return self._build_tree(all_cats)

    def update(
        self,
        id: int,
        *,
        name: str | None = None,
        icon: str | None = None,
        sort_order: int | None = None,
        parent_id: int | None = None,
    ) -> dict:
        """Update a category. Only supplied fields are changed."""
        cat = self.get_by_id(id)  # raises if not found

        fields: list[str] = []
        values: list = []

        if name is not None:
            fields.append("name = ?")
            values.append(name)
        if icon is not None:
            fields.append("icon = ?")
            values.append(icon)
        if sort_order is not None:
            fields.append("sort_order = ?")
            values.append(sort_order)
        if parent_id is not None:
            # Validate parent exists and same type
            parent = self.db.execute(
                "SELECT id, type_id FROM categories WHERE id = ?", (parent_id,)
            ).fetchone()
            if parent is None:
                raise ValueError(f"Parent category {parent_id} does not exist")
            if parent["type_id"] != cat["type_id"]:
                raise ValueError(
                    f"Parent category {parent_id} does not belong to type {cat['type_id']}"
                )
            # Prevent self-reference
            if parent_id == id:
                raise ValueError("A category cannot be its own parent")
            # Prevent circular reference
            if self._is_ancestor(id, parent_id):
                raise ValueError(
                    f"Category {parent_id} is a descendant of {id}, cannot set as parent"
                )
            fields.append("parent_id = ?")
            values.append(parent_id)

        if not fields:
            return cat

        fields.append("updated_at = datetime('now')")
        values.append(id)
        self.db.execute(
            f"UPDATE categories SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        self.db.commit()
        return self.get_by_id(id)

    def delete(self, id: int) -> None:
        """Delete a category. Fails if it has children or linked assets."""
        self.get_by_id(id)  # raises if not found

        child_count = self.db.execute(
            "SELECT COUNT(*) FROM categories WHERE parent_id = ?", (id,)
        ).fetchone()[0]
        if child_count > 0:
            raise ValueError(
                f"Cannot delete category {id}: has {child_count} child categories"
            )

        asset_count = self.db.execute(
            "SELECT COUNT(*) FROM assets WHERE category_id = ?", (id,)
        ).fetchone()[0]
        if asset_count > 0:
            raise ValueError(
                f"Cannot delete category {id}: has {asset_count} linked assets"
            )

        self.db.execute("DELETE FROM categories WHERE id = ?", (id,))
        self.db.commit()

    # ------------------------------------------------------------------
    # Import/export helpers
    # ------------------------------------------------------------------

    def find_by_name(self, name: str, type_id: int = 1) -> dict | None:
        """Find a category by name within a given type. Returns None if not found."""
        row = self.db.execute(
            "SELECT * FROM categories WHERE name = ? AND type_id = ?",
            (name, type_id),
        ).fetchone()
        return dict(row) if row else None

    def create_simple(self, name: str, type_id: int = 1) -> dict:
        """Create a simple category with just a name and type. Alias for create()."""
        return self.create(type_id=type_id, name=name)

    def list_fields(self, category_id: int) -> list[dict]:
        """List custom fields defined for a category (from category_fields table)."""
        rows = self.db.execute(
            "SELECT * FROM category_fields WHERE category_id = ? ORDER BY sort_order, id",
            (category_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def create_field(
        self, category_id: int, field_name: str, field_type: str = "text"
    ) -> dict:
        """Create a new custom field definition for a category."""
        cur = self.db.execute(
            "INSERT INTO category_fields (category_id, field_name, field_type) "
            "VALUES (?, ?, ?)",
            (category_id, field_name, field_type),
        )
        self.db.commit()
        row = self.db.execute(
            "SELECT * FROM category_fields WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def verify_type_exists(self, type_id: int) -> None:
        """Raise ValueError if *type_id* does not exist in asset_types."""
        row = self.db.execute(
            "SELECT id FROM asset_types WHERE id = ?", (type_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Asset type {type_id} not found")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_tree(cats: list[dict]) -> list[dict]:
        """Build a nested tree from a flat list of categories."""
        m = {c["id"]: c for c in cats}
        roots: list[dict] = []
        for c in cats:
            c["children"] = []
        for c in cats:
            if c["parent_id"] is None:
                roots.append(c)
            elif c["parent_id"] in m:
                m[c["parent_id"]]["children"].append(c)
        return roots

    def _is_ancestor(self, ancestor_id: int, descendant_id: int) -> bool:
        """Return True if *ancestor_id* is an ancestor of *descendant_id*."""
        current_id = descendant_id
        visited: set[int] = set()
        while current_id is not None:
            if current_id == ancestor_id:
                return True
            if current_id in visited:
                break  # safety: avoid infinite loop on corrupt data
            visited.add(current_id)
            row = self.db.execute(
                "SELECT parent_id FROM categories WHERE id = ?", (current_id,)
            ).fetchone()
            current_id = row["parent_id"] if row else None
        return False
