from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TransactionCategory(BaseModel):
    id: int
    name: str
    icon: str = ''
    type: str  # 'income' | 'expense'
    parent_id: int | None = None
    sort_order: int = 0


class CreateTransactionCategoryRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    icon: str = Field(default='', max_length=50)
    type: Literal['income', 'expense']
    parent_id: int | None = None
    sort_order: int = Field(default=0, ge=0)


class UpdateTransactionCategoryRequest(BaseModel):
    name: str | None = None
    icon: str | None = None
    sort_order: int | None = None


class Account(BaseModel):
    id: int
    name: str
    type: str
    balance: float = 0
    icon: str = ''
    notes: str = ''
    sort_order: int = 0
    is_active: bool = True


class CreateAccountRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: Literal['cash', 'bank', 'wechat', 'alipay', 'credit', 'other']
    balance: float = Field(default=0, ge=0)
    icon: str = Field(default='', max_length=50)
    notes: str = Field(default='', max_length=500)
    sort_order: int = Field(default=0, ge=0)


class UpdateAccountRequest(BaseModel):
    name: str | None = None
    type: str | None = None
    balance: float | None = None
    icon: str | None = None
    notes: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class Transaction(BaseModel):
    id: int
    type: str
    amount: float
    category_id: int | None = None
    account_id: int | None = None
    to_account_id: int | None = None
    transaction_date: str
    merchant: str = ''
    note: str = ''
    source: str = 'manual'
    original_id: str = ''
    created_at: str = ''
    updated_at: str = ''
    # Joined fields (optional, for list view)
    category_name: str = ''
    category_icon: str = ''
    account_name: str = ''


class CreateTransactionRequest(BaseModel):
    type: Literal['income', 'expense', 'transfer']
    amount: float = Field(ge=0, description="金额（非负）")
    category_id: int | None = None
    account_id: int | None = None
    to_account_id: int | None = None
    transaction_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$', description="交易日期 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
    merchant: str = Field(default='', max_length=500)
    note: str = Field(default='', max_length=2000)

    @model_validator(mode='after')
    def validate_transfer_fields(self):
        if self.type == 'transfer':
            if not self.account_id:
                raise ValueError('转账必须指定转出账户')
            if not self.to_account_id:
                raise ValueError('转账必须指定转入账户')
            if self.account_id == self.to_account_id:
                raise ValueError('转出账户和转入账户不能相同')
        if self.type in ('income', 'expense') and self.amount == 0:
            raise ValueError('收入/支出金额必须大于0')
        return self


class UpdateTransactionRequest(BaseModel):
    type: Literal['income', 'expense', 'transfer'] | None = None
    amount: float | None = Field(default=None, ge=0)
    category_id: int | None = None
    account_id: int | None = None
    to_account_id: int | None = None
    transaction_date: str | None = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$')
    merchant: str | None = Field(default=None, max_length=500)
    note: str | None = Field(default=None, max_length=2000)


class TransactionStats(BaseModel):
    total_income: float = 0
    total_expense: float = 0
    balance: float = 0
    transaction_count: int = 0
    category_breakdown: list[dict] = []
