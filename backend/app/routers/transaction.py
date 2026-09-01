from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query, UploadFile, File

from backend.app.models.common import ok, ok_list, error
from backend.app.models.transaction import (
    CreateTransactionRequest,
    UpdateTransactionRequest,
)
from backend.app.services.transaction import TransactionService
from backend.app.services.bill_parser import (
    parse_wechat_bill,
    parse_alipay_bill,
    BillParseError,
)

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


def create_transaction_router(svc: TransactionService) -> APIRouter:
    router = APIRouter(tags=["记账管理"])

    @router.get("/", summary="获取交易记录列表")
    def list_transactions(
        type: str = "",
        category_id: int | None = None,
        account_id: int | None = None,
        date_from: str = "",
        date_to: str = "",
        search: str = "",
        sort_by: str = "",
        sort_order: str = "",
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ):
        items, total = svc.list(
            type=type, category_id=category_id, account_id=account_id,
            date_from=date_from, date_to=date_to, search=search,
            sort_by=sort_by, sort_order=sort_order,
            page=page, page_size=page_size,
        )
        return ok_list(items, total, page, page_size)

    @router.get("/stats", summary="获取交易统计")
    def get_stats(
        date_from: str = "",
        date_to: str = "",
    ):
        return ok(svc.get_stats(date_from, date_to))

    @router.get("/{id}", summary="获取交易详情")
    def get_transaction(id: int):
        try:
            return ok(svc.get_by_id(id))
        except ValueError:
            raise HTTPException(404, detail=error(40401, f"Transaction {id} not found"))

    @router.post("/", status_code=201, summary="创建交易记录")
    def create_transaction(req: CreateTransactionRequest):
        txn = svc.create(
            type=req.type, amount=req.amount, category_id=req.category_id,
            account_id=req.account_id, to_account_id=req.to_account_id,
            transaction_date=req.transaction_date, merchant=req.merchant,
            note=req.note,
        )
        return ok(txn)

    @router.put("/{id}", summary="更新交易记录")
    def update_transaction(id: int, req: UpdateTransactionRequest):
        try:
            txn = svc.update(id, req)
            return ok(txn)
        except ValueError:
            raise HTTPException(404, detail=error(40401, f"Transaction {id} not found"))

    @router.delete("/{id}", summary="删除交易记录")
    def delete_transaction(id: int):
        try:
            svc.delete(id)
            return ok()
        except ValueError:
            raise HTTPException(404, detail=error(40401, f"Transaction {id} not found"))

    @router.post("/batch-delete", summary="批量删除交易记录")
    def batch_delete_transactions(ids: list[int] = Body(..., embed=True)):
        deleted = svc.batch_delete(ids)
        return ok({"deleted": deleted})

    # ── Bill import endpoints ─────────────────────────────────

    def _read_with_size_limit(raw: bytes) -> str:
        """Check size limit and decode CSV content."""
        if len(raw) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=error(41301, "文件过大，最大支持 10MB"),
            )
        try:
            return raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                return raw.decode("gbk")
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail=error(40001, "文件编码不支持，请使用 UTF-8 或 GBK 编码"),
                )

    @router.post("/import/wechat", status_code=201, summary="从微信账单导入交易记录")
    async def import_wechat_bill(
        file: UploadFile = File(...),
        account_id: int | None = Query(None, description="关联账户 ID"),
    ):
        raw = await file.read()
        content = _read_with_size_limit(raw)
        try:
            parsed = parse_wechat_bill(content)
        except BillParseError as exc:
            raise HTTPException(400, detail=error(40001, str(exc)))
        result = svc.import_transactions(parsed, source="import_wechat",
                                        default_account_id=account_id)
        return ok(result)

    @router.post("/import/alipay", status_code=201, summary="从支付宝账单导入交易记录")
    async def import_alipay_bill(
        file: UploadFile = File(...),
        account_id: int | None = Query(None, description="关联账户 ID"),
    ):
        raw = await file.read()
        content = _read_with_size_limit(raw)
        try:
            parsed = parse_alipay_bill(content)
        except BillParseError as exc:
            raise HTTPException(400, detail=error(40001, str(exc)))
        result = svc.import_transactions(parsed, source="import_alipay",
                                        default_account_id=account_id)
        return ok(result)

    return router
