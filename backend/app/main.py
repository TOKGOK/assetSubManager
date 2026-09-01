from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import load_config
from backend.app.database import init_db, get_db
from backend.app.auth import verify_token, create_auth_routes
from backend.app.repositories.audit import AuditRepo
from backend.app.repositories.transaction import TransactionRepo
from backend.app.repositories.transaction_category import TransactionCategoryRepo
from backend.app.repositories.account import AccountRepo
from backend.app.repositories.subscription_period import SubscriptionPeriodRepo
from backend.app.repositories.asset_type import AssetTypeRepo
from backend.app.repositories.asset import AssetRepo
from backend.app.repositories.category import CategoryRepo
from backend.app.services.subscription_period import SubscriptionPeriodService
from backend.app.services.transaction import TransactionService
from backend.app.services.transaction_category import TransactionCategoryService
from backend.app.services.account import AccountService
from backend.app.services.asset_type import AssetTypeService
from backend.app.services.asset import AssetService
from backend.app.services.category import CategoryService
from backend.app.routers.subscription_period import create_subscription_period_router
from backend.app.routers.dashboard import create_dashboard_router
from backend.app.routers.audit import create_audit_router
from backend.app.routers.import_export import create_import_export_router
from backend.app.routers.transaction import create_transaction_router
from backend.app.routers.transaction_category import create_transaction_category_router
from backend.app.routers.account import create_account_router
from backend.app.routers.asset_type import create_asset_type_router
from backend.app.routers.asset import create_asset_router
from backend.app.routers.category import create_type_scoped_router, create_detail_router
from backend.app.services.import_export import ImportExportService
from backend.app.services.dashboard import DashboardService

logger = logging.getLogger(__name__)


def setup_routes():
    """Register all API routes. Safe to call multiple times (e.g. in tests)."""
    # Clear previous routes AND reset lifespan to avoid accumulating nested
    # lifespan wrappers from repeated include_router() calls.
    app.routes.clear()
    app.dependency_overrides.clear()
    app.router.lifespan_context = _original_lifespan

    db = get_db()
    audit_repo = AuditRepo(db)
    txn_repo = TransactionRepo(db)
    txn_cat_repo = TransactionCategoryRepo(db)
    account_repo = AccountRepo(db)
    period_repo = SubscriptionPeriodRepo(db)
    asset_type_repo = AssetTypeRepo()
    unified_cat_repo = CategoryRepo(db)
    unified_asset_repo = AssetRepo(db)

    period_svc = SubscriptionPeriodService(period_repo, audit_repo)
    txn_svc = TransactionService(txn_repo, account_repo, audit_repo)
    txn_cat_svc = TransactionCategoryService(txn_cat_repo, audit_repo)
    account_svc = AccountService(account_repo, audit_repo)

    asset_type_svc = AssetTypeService(asset_type_repo, audit_repo)
    unified_cat_svc = CategoryService(unified_cat_repo, audit_repo)
    unified_asset_svc = AssetService(unified_asset_repo, audit_repo)

    dashboard_svc = DashboardService(unified_asset_repo)

    # Auth routes — no auth dependency
    app.include_router(create_auth_routes())

    # Business routes — all require auth when enabled
    auth_deps = [Depends(verify_token)]

    app.include_router(
        create_dashboard_router(dashboard_svc), prefix="/api/v1/dashboard",
        dependencies=auth_deps,
    )
    app.include_router(
        create_audit_router(audit_repo), prefix="/api/v1/audit-log",
        dependencies=auth_deps,
    )
    ie_svc = ImportExportService(unified_asset_repo, unified_cat_repo, audit_repo)
    app.include_router(
        create_import_export_router(ie_svc), prefix="/api/v1",
        dependencies=auth_deps,
    )
    app.include_router(
        create_transaction_router(txn_svc), prefix="/api/v1/transactions",
        dependencies=auth_deps,
    )
    app.include_router(
        create_transaction_category_router(txn_cat_svc), prefix="/api/v1/transaction-categories",
        dependencies=auth_deps,
    )
    app.include_router(
        create_account_router(account_svc), prefix="/api/v1/accounts",
        dependencies=auth_deps,
    )
    app.include_router(
        create_subscription_period_router(period_svc),
        prefix="/api/v1/subscription-periods",
        dependencies=auth_deps,
    )
    app.include_router(
        create_asset_type_router(asset_type_svc),
        prefix="/api/v1/asset-types",
        dependencies=auth_deps,
    )
    app.include_router(
        create_type_scoped_router(unified_cat_svc),
        prefix="/api/v1/asset-types/{type_id}/categories",
        dependencies=auth_deps,
    )
    app.include_router(
        create_detail_router(unified_cat_svc),
        prefix="/api/v1/categories",
        dependencies=auth_deps,
    )
    app.include_router(
        create_asset_router(unified_asset_svc),
        prefix="/api/v1/assets",
        dependencies=auth_deps,
    )

    @app.get("/api/v1/health")
    def health():
        return {"code": 0, "data": {"status": "ok"}, "message": "success"}

    # Serve React build if available
    _static_dir = Path(__file__).parent / "static"
    if _static_dir.exists() and (_static_dir / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=str(_static_dir)), name="static-assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = _static_dir / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(_static_dir / "index.html")


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    cfg = load_config()
    logging.basicConfig(
        level=getattr(logging, cfg.log_level.upper(), logging.INFO)
    )
    logger.info(f"Starting asset manager: listen={cfg.listen_addr}, data_dir={cfg.data_dir}")
    init_db(cfg)
    setup_routes()
    yield


app = FastAPI(
    title="Asset Manager",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "认证", "description": "用户登录与认证状态管理"},
        {"name": "仪表盘", "description": "汇总资产与订阅的概览数据"},
        {"name": "审计日志", "description": "查看系统操作审计日志"},
        {"name": "导入导出", "description": "资产的 CSV/JSON/SQL 导入与导出"},
        {"name": "记账管理", "description": "收支记录的增删改查、统计分析"},
        {"name": "记账分类", "description": "收支分类的增删改查"},
        {"name": "账户管理", "description": "账户（银行卡/微信/支付宝等）的增删改查"},
        {"name": "订阅周期配置", "description": "订阅周期配置的增删改查"},
        {"name": "资产类型管理", "description": "统一资产类型的增删改查、字段配置管理"},
        {"name": "统一分类管理", "description": "按资产类型管理的统一分类树，支持分类的增删改查"},
        {"name": "统一资产管理", "description": "统一资产的增删改查，支持自定义字段、计算字段、筛选搜索"},
    ],
)

# Save original lifespan so setup_routes() can reset it on repeated calls.
# Each include_router() wraps the lifespan one layer deeper; without resetting,
# repeated setup_routes() calls (as in tests) eventually cause recursion errors.
_original_lifespan = app.router.lifespan_context


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return Pydantic validation errors in the project's standard error format."""
    messages = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err["loc"] if x != "body")
        msg = err["msg"]
        messages.append(f"{loc}: {msg}" if loc else msg)
    return JSONResponse(
        status_code=422,
        content={"code": 42200, "data": None, "message": "; ".join(messages)},
    )


# CORS: configurable origins (comma-separated via CORS_ORIGINS env var)
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn
    cfg = load_config()
    host, _, port = cfg.listen_addr.rpartition(":")
    uvicorn.run(
        "backend.app.main:app",
        host=host or "127.0.0.1",
        port=int(port or 8080),
        reload=True,
    )
