from pydantic import BaseModel


class AuditLog(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    changed_fields: str = "{}"
    timestamp: str = ""


class AuditLogFilter(BaseModel):
    entity_type: str = ""
    action: str = ""
    page: int = 1
    page_size: int = 20
