"""Simple token-based authentication."""
from __future__ import annotations

import hashlib

from fastapi import Request, HTTPException

from backend.app.config import load_config

_token: str | None = None


def _get_token() -> str:
    global _token
    if _token is None:
        cfg = load_config()
        _token = hashlib.sha256(
            f"{cfg.auth_password}:asset-manager-secret".encode()
        ).hexdigest()
    return _token


def reset_token() -> None:
    """Reset cached token — useful in tests when config changes."""
    global _token
    _token = None


def verify_token(request: Request) -> None:
    """Dependency that rejects unauthenticated requests when auth is enabled."""
    cfg = load_config()
    if not cfg.auth_enabled:
        return
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail={"code": 401, "message": "未授权"}
        )
    token = auth_header[7:]
    if token != _get_token():
        raise HTTPException(
            status_code=401, detail={"code": 401, "message": "令牌无效"}
        )


def create_auth_routes():
    """Create auth router with login / status endpoints."""
    from fastapi import APIRouter

    from backend.app.models.common import ok

    router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

    @router.post("/login", summary="用户登录", description="验证密码并返回访问令牌")
    def login(request_data: dict):
        cfg = load_config()
        password = request_data.get("password", "")
        if not cfg.auth_enabled:
            return ok({"token": "", "auth_enabled": False})
        if password != cfg.auth_password:
            raise HTTPException(
                status_code=401, detail={"code": 401, "message": "密码错误"}
            )
        return ok({"token": _get_token(), "auth_enabled": True})

    @router.get("/status", summary="获取认证状态", description="返回当前系统是否启用认证")
    def auth_status():
        cfg = load_config()
        return ok({"auth_enabled": cfg.auth_enabled})

    return router
