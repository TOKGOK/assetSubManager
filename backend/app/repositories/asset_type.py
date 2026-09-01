"""AssetType CRUD repository using SQLAlchemy ORM."""
from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models.asset_type import AssetTypeORM
from backend.app.orm_base import get_session


class AssetTypeRepo:
    """资产类型数据访问层（基于 SQLAlchemy ORM）。"""

    def __init__(self) -> None:
        pass

    # -- helpers --------------------------------------------------------------

    @staticmethod
    def _to_dict(obj: AssetTypeORM) -> dict:
        """Convert an ORM model instance to a plain dict."""
        return {
            "id": obj.id,
            "name": obj.name,
            "icon": obj.icon or "",
            "field_config": obj.field_config or {},
            "is_system": bool(obj.is_system),
            "created_at": (
                obj.created_at.isoformat()
                if hasattr(obj.created_at, "isoformat")
                else str(obj.created_at or "")
            ),
            "updated_at": (
                obj.updated_at.isoformat()
                if hasattr(obj.updated_at, "isoformat")
                else str(obj.updated_at or "")
            ),
        }

    # -- CRUD -----------------------------------------------------------------

    def create(
        self,
        name: str,
        icon: str = "",
        field_config: dict | None = None,
        is_system: bool = False,
    ) -> dict:
        """Create a new asset type.  Returns the created row as dict."""
        session: Session = get_session()
        try:
            obj = AssetTypeORM(
                name=name,
                icon=icon,
                field_config=field_config if field_config is not None else {},
                is_system=is_system,
            )
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return self._to_dict(obj)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(self, id: int) -> dict:
        """Return a single asset type by id, or raise ``ValueError``."""
        session: Session = get_session()
        try:
            obj = session.get(AssetTypeORM, id)
            if obj is None:
                raise ValueError(f"AssetType {id} not found")
            return self._to_dict(obj)
        finally:
            session.close()

    def list_all(self) -> list[dict]:
        """Return all asset types ordered by id."""
        session: Session = get_session()
        try:
            rows = (
                session.query(AssetTypeORM)
                .order_by(AssetTypeORM.id)
                .all()
            )
            return [self._to_dict(r) for r in rows]
        finally:
            session.close()

    def find_by_name(self, name: str) -> dict | None:
        """Return the first asset type with the given name, or ``None``."""
        session: Session = get_session()
        try:
            obj = (
                session.query(AssetTypeORM)
                .filter(AssetTypeORM.name == name)
                .first()
            )
            return self._to_dict(obj) if obj else None
        finally:
            session.close()

    def update(self, id: int, **kwargs) -> dict:
        """Update fields of an asset type.  Raises ``ValueError`` if not found."""
        session: Session = get_session()
        try:
            obj = session.get(AssetTypeORM, id)
            if obj is None:
                raise ValueError(f"AssetType {id} not found")
            for key in ("name", "icon", "field_config", "is_system"):
                if key in kwargs:
                    setattr(obj, key, kwargs[key])
            session.commit()
            session.refresh(obj)
            return self._to_dict(obj)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, id: int) -> None:
        """Delete an asset type.  Raises ``ValueError`` if not found."""
        session: Session = get_session()
        try:
            obj = session.get(AssetTypeORM, id)
            if obj is None:
                raise ValueError(f"AssetType {id} not found")
            session.delete(obj)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
