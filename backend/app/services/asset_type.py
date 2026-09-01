"""AssetType business-logic service."""
from __future__ import annotations

from backend.app.repositories.asset_type import AssetTypeRepo
from backend.app.repositories.audit import AuditRepo

# Allowed values for field.type inside field_config.
VALID_FIELD_TYPES = {
    "text", "number", "boolean", "date", "datetime",
    "select", "textarea", "relation", "computed",
}


def _validate_field_config(field_config: dict) -> None:
    """Raise ``ValueError`` when *field_config* has an invalid structure.

    Expected structure::

        {
            "fields": [
                {"key": "…", "label": "…", "type": "text", …},
                …
            ]
        }
    """
    if not isinstance(field_config, dict):
        raise ValueError("field_config must be a JSON object")

    fields = field_config.get("fields")
    if fields is None:
        return  # empty config {} is acceptable

    if not isinstance(fields, list):
        raise ValueError("field_config.fields must be a list")

    for idx, field in enumerate(fields):
        if not isinstance(field, dict):
            raise ValueError(f"field_config.fields[{idx}] must be an object")
        for required_key in ("key", "label", "type"):
            if required_key not in field:
                raise ValueError(
                    f"field_config.fields[{idx}] missing required key '{required_key}'"
                )
        if field["type"] not in VALID_FIELD_TYPES:
            raise ValueError(
                f"field_config.fields[{idx}].type '{field['type']}' is not valid. "
                f"Allowed: {', '.join(sorted(VALID_FIELD_TYPES))}"
            )


class AssetTypeService:
    """资产类型业务逻辑层。"""

    def __init__(self, repo: AssetTypeRepo, audit: AuditRepo) -> None:
        self.repo = repo
        self.audit = audit

    # -- read -----------------------------------------------------------------

    def list(self) -> list[dict]:
        return self.repo.list_all()

    def get_by_id(self, id: int) -> dict:
        return self.repo.get_by_id(id)

    # -- create ---------------------------------------------------------------

    def create(
        self,
        name: str,
        icon: str = "",
        field_config: dict | None = None,
        is_system: bool = False,
    ) -> dict:
        """Create a new asset type.

        Validations:
        * *name* must be unique.
        * *field_config* structure must be correct.
        * Setting *is_system* = True via API is forbidden (returns ValueError).
        """
        # Name uniqueness
        existing = self.repo.find_by_name(name)
        if existing:
            raise ValueError(f"Asset type name '{name}' already exists")

        # field_config structure
        fc = field_config if field_config is not None else {}
        _validate_field_config(fc)

        # Prevent creating system types through the API
        if is_system:
            raise ValueError("Cannot create system asset types via API")

        result = self.repo.create(
            name=name, icon=icon, field_config=fc, is_system=False,
        )
        self.audit.log("asset_type", result["id"], "create", {"name": name})
        return result

    # -- update ---------------------------------------------------------------

    def update(self, id: int, **kwargs) -> dict:
        """Update an asset type.

        * Rejects *is_system* changes.
        * Validates *name* uniqueness (if changed).
        * Validates *field_config* structure (if changed).
        """
        # Ensure the row exists (raises ValueError → 404 in router)
        self.repo.get_by_id(id)

        # Reject is_system modification
        if "is_system" in kwargs:
            del kwargs["is_system"]

        # Name uniqueness (if being changed)
        if "name" in kwargs and kwargs["name"] is not None:
            existing = self.repo.find_by_name(kwargs["name"])
            if existing and existing["id"] != id:
                raise ValueError(
                    f"Asset type name '{kwargs['name']}' already exists"
                )

        # field_config structure (if being changed)
        if "field_config" in kwargs and kwargs["field_config"] is not None:
            _validate_field_config(kwargs["field_config"])

        result = self.repo.update(id, **kwargs)
        self.audit.log("asset_type", id, "update", {"name": kwargs.get("name")})
        return result

    # -- delete ---------------------------------------------------------------

    def delete(self, id: int) -> None:
        """Delete an asset type.

        * System types (``is_system=True``) cannot be deleted → ``ValueError``
          with message containing "系统预设".
        * Non-existent id → ``ValueError`` with message containing "not found".
        """
        asset_type = self.repo.get_by_id(id)  # raises ValueError if not found
        if asset_type["is_system"]:
            raise ValueError("系统预设资产类型不可删除")
        self.repo.delete(id)
        self.audit.log("asset_type", id, "delete")
