from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse

from backend.app.models.common import ok, error
from backend.app.services.import_export import ImportExportService

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


def create_import_export_router(svc: ImportExportService) -> APIRouter:
    router = APIRouter(tags=["导入导出"])

    # ── Export endpoints ──────────────────────────────────────

    @router.get("/export/csv", summary="导出资产为 CSV 文件")
    def export_csv():
        content = svc.export_csv()
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=assets.csv"},
        )

    @router.get("/export/json", summary="导出资产为 JSON 文件")
    def export_json():
        content = svc.export_json()
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=assets.json"},
        )

    @router.get("/export/sql", summary="导出资产为 SQL 备份文件")
    def export_sql():
        content = svc.export_sql()
        return PlainTextResponse(
            content,
            headers={"Content-Disposition": "attachment; filename=backup.sql"},
        )

    # ── Import endpoints ──────────────────────────────────────

    async def _read_upload_with_limit(file: UploadFile) -> str:
        raw = await file.read()
        if len(raw) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=error(41301, "文件过大，最大支持 10MB"),
            )
        return raw.decode("utf-8")

    @router.post("/import/csv", status_code=201, summary="从 CSV 文件导入资产")
    async def import_csv(file: UploadFile = File(...)):
        content = await _read_upload_with_limit(file)
        result = svc.import_csv(content)
        return ok(result)

    @router.post("/import/json", status_code=201, summary="从 JSON 文件导入资产")
    async def import_json(file: UploadFile = File(...)):
        content = await _read_upload_with_limit(file)
        result = svc.import_json(content)
        return ok(result)

    @router.post("/import/sql", status_code=201, summary="从 SQL 文件导入资产")
    async def import_sql(file: UploadFile = File(...)):
        content = await _read_upload_with_limit(file)
        result = svc.import_sql(content)
        return ok(result)

    return router
