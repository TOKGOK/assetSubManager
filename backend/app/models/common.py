from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    data: T | None = None
    message: str = "success"


class ListData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


def ok(data: Any = None) -> dict:
    return {"code": 0, "data": data, "message": "success"}


def ok_list(items: list, total: int, page: int, page_size: int) -> dict:
    return ok({"items": items, "total": total, "page": page, "page_size": page_size})


def error(code: int, message: str) -> dict:
    return {"code": code, "data": None, "message": message}
