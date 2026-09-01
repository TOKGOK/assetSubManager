from __future__ import annotations

import csv
from dataclasses import dataclass


@dataclass
class ParsedTransaction:
    """解析后的交易记录"""
    type: str          # 'income' | 'expense'
    amount: float
    transaction_date: str   # ISO date: YYYY-MM-DD
    merchant: str
    note: str
    original_id: str        # 原始交易单号，用于去重


class BillParseError(Exception):
    """账单解析错误"""
    pass


# ---------------------------------------------------------------------------
# WeChat Pay
# ---------------------------------------------------------------------------

def parse_wechat_bill(content: str) -> list[ParsedTransaction]:
    """解析微信支付导出的 CSV 账单"""
    # Strip BOM
    if content.startswith('﻿'):
        content = content[1:]

    lines = content.strip().splitlines()

    # Locate header row — the one containing '交易时间'
    header_idx = None
    for i, line in enumerate(lines):
        if '交易时间' in line:
            header_idx = i
            break
    if header_idx is None:
        raise BillParseError("无法识别微信支付账单格式：未找到表头")

    reader = csv.DictReader(lines[header_idx:])
    transactions: list[ParsedTransaction] = []

    _OK_STATUSES = {'支付成功', '已收款', '转账成功', '已退款'}

    for row in reader:
        tx_time = (row.get('交易时间') or '').strip()
        if not tx_time:
            continue

        status = (row.get('当前状态') or '').strip()
        if status not in _OK_STATUSES:
            continue

        # Amount
        amount_str = (row.get('金额(元)') or '0').replace('¥', '').replace(',', '').strip()
        try:
            amount = float(amount_str)
        except ValueError:
            continue
        if amount <= 0:
            continue

        # Type
        tx_type_raw = (row.get('交易类型') or '').strip()
        if tx_type_raw in ('支出',):
            tx_type = 'expense'
        elif tx_type_raw in ('收入', '已退款'):
            tx_type = 'income'
        else:
            tx_type = 'expense'

        # Date — take first 10 chars (YYYY-MM-DD)
        tx_date = tx_time[:10]

        original_id = (row.get('交易单号') or '').strip()
        if not original_id:
            continue

        transactions.append(ParsedTransaction(
            type=tx_type,
            amount=amount,
            transaction_date=tx_date,
            merchant=(row.get('交易对方') or '').strip(),
            note=(row.get('商品') or '').strip(),
            original_id=original_id,
        ))

    return transactions


# ---------------------------------------------------------------------------
# Alipay
# ---------------------------------------------------------------------------

def parse_alipay_bill(content: str) -> list[ParsedTransaction]:
    """解析支付宝导出的 CSV 账单"""
    # Strip BOM
    if content.startswith('﻿'):
        content = content[1:]

    lines = content.strip().splitlines()

    # Locate header row — must contain both '交易号' and '交易创建时间'
    header_idx = None
    for i, line in enumerate(lines):
        if '交易号' in line and '交易创建时间' in line:
            header_idx = i
            break
    if header_idx is None:
        raise BillParseError("无法识别支付宝账单格式：未找到表头")

    reader = csv.DictReader(lines[header_idx:])
    transactions: list[ParsedTransaction] = []

    _OK_STATUSES = {'交易成功', '退款成功'}

    for row in reader:
        txn_id = (row.get('交易号') or '').strip()
        if not txn_id:
            continue

        status = (row.get('交易状态') or '').strip()
        if status not in _OK_STATUSES:
            continue

        # Amount
        amount_str = (row.get('金额（元）') or '0').replace(',', '').strip()
        try:
            amount = float(amount_str)
        except ValueError:
            continue
        if amount <= 0:
            continue

        # Direction
        direction = (row.get('收/支') or '').strip()
        if direction == '支出':
            tx_type = 'expense'
        elif direction == '收入':
            tx_type = 'income'
        else:
            # '不计收支', '退款' etc. — skip
            continue

        # Date
        raw_date = (row.get('交易创建时间') or '').strip()
        tx_date = raw_date[:10]

        transactions.append(ParsedTransaction(
            type=tx_type,
            amount=amount,
            transaction_date=tx_date,
            merchant=(row.get('交易对方') or '').strip(),
            note=(row.get('商品') or '').strip(),
            original_id=txn_id,
        ))

    return transactions
