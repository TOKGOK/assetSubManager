import json
import os
import sqlite3
import logging
from pathlib import Path

from backend.app.config import Config

logger = logging.getLogger(__name__)

MIGRATION_SQL = """
-- 实体资产分类表（原 categories 表，现仅用于实体资产）
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER DEFAULT NULL REFERENCES categories(id) ON DELETE SET NULL,
    icon TEXT DEFAULT '',
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- 实体资产自定义字段表
CREATE TABLE IF NOT EXISTS category_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    field_type TEXT NOT NULL CHECK(field_type IN ('text', 'number', 'date', 'select', 'boolean')),
    required INTEGER DEFAULT 0,
    default_value TEXT DEFAULT '',
    options TEXT DEFAULT '{}',
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now'))
);

-- 实体资产表
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    purchase_date TEXT DEFAULT '',
    purchase_price REAL DEFAULT 0,
    current_value REAL DEFAULT 0,
    currency TEXT DEFAULT 'CNY',
    notes TEXT DEFAULT '',
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'sold', 'disposed')),
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- 实体资产自定义字段值表
CREATE TABLE IF NOT EXISTS asset_field_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    category_field_id INTEGER NOT NULL REFERENCES category_fields(id) ON DELETE CASCADE,
    value TEXT DEFAULT '',
    UNIQUE(asset_id, category_field_id)
);

-- 实体资产估值历史表
CREATE TABLE IF NOT EXISTS asset_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    value REAL NOT NULL,
    recorded_at DATETIME DEFAULT (datetime('now')),
    source TEXT DEFAULT 'manual' CHECK(source IN ('manual', 'import')),
    notes TEXT DEFAULT ''
);

-- 实体资产附件表
CREATE TABLE IF NOT EXISTS asset_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    mime_type TEXT DEFAULT '',
    size INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now'))
);

-- 虚拟资产分类表
CREATE TABLE IF NOT EXISTS virtual_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER DEFAULT NULL REFERENCES virtual_categories(id) ON DELETE SET NULL,
    icon TEXT DEFAULT '',
    description TEXT DEFAULT '',
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- 虚拟资产自定义字段表
CREATE TABLE IF NOT EXISTS virtual_category_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES virtual_categories(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    field_type TEXT NOT NULL CHECK(field_type IN ('text', 'number', 'date', 'select', 'boolean')),
    required INTEGER DEFAULT 0,
    default_value TEXT DEFAULT '',
    options TEXT DEFAULT '{}',
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now'))
);

-- 虚拟资产表
CREATE TABLE IF NOT EXISTS virtual_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES virtual_categories(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    account_name TEXT DEFAULT '',
    password TEXT DEFAULT '',
    license_key TEXT DEFAULT '',
    expiry_date TEXT DEFAULT '',
    platform TEXT DEFAULT '',
    url TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'expired', 'cancelled')),
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- 虚拟资产自定义字段值表
CREATE TABLE IF NOT EXISTS virtual_asset_field_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES virtual_assets(id) ON DELETE CASCADE,
    field_id INTEGER NOT NULL REFERENCES virtual_category_fields(id) ON DELETE CASCADE,
    value TEXT DEFAULT '',
    UNIQUE(asset_id, field_id)
);

-- 订阅分类表
CREATE TABLE IF NOT EXISTS subscription_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER DEFAULT NULL REFERENCES subscription_categories(id) ON DELETE SET NULL,
    icon TEXT DEFAULT '',
    description TEXT DEFAULT '',
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- 订阅自定义字段表
CREATE TABLE IF NOT EXISTS subscription_category_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES subscription_categories(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    field_type TEXT NOT NULL CHECK(field_type IN ('text', 'number', 'date', 'select', 'boolean')),
    required INTEGER DEFAULT 0,
    default_value TEXT DEFAULT '',
    options TEXT DEFAULT '{}',
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now'))
);

-- 订阅表
CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER DEFAULT NULL REFERENCES subscription_categories(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0,
    currency TEXT DEFAULT 'CNY',
    cycle TEXT DEFAULT 'monthly',
    period_id INTEGER DEFAULT NULL REFERENCES subscription_periods(id) ON DELETE SET NULL,
    start_date TEXT NOT NULL,
    next_renewal TEXT DEFAULT '',
    auto_renew INTEGER DEFAULT 0,
    reminder_days INTEGER DEFAULT 7,
    notes TEXT DEFAULT '',
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'cancelled', 'expired')),
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- 订阅自定义字段值表
CREATE TABLE IF NOT EXISTS subscription_field_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    field_id INTEGER NOT NULL REFERENCES subscription_category_fields(id) ON DELETE CASCADE,
    value TEXT DEFAULT '',
    UNIQUE(subscription_id, field_id)
);

-- 订阅续费日志表
CREATE TABLE IF NOT EXISTS sub_renewal_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    renewed_at DATETIME NOT NULL,
    amount REAL NOT NULL DEFAULT 0,
    method TEXT DEFAULT '',
    notes TEXT DEFAULT ''
);

-- 订阅周期配置表
CREATE TABLE IF NOT EXISTS subscription_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    rule_type TEXT NOT NULL CHECK(rule_type IN (
        'daily_interval',   -- 每 X 天
        'monthly_day',      -- 每月 X 日
        'yearly_date',      -- 每年 X 月 X 日
        'custom'            -- 自定义组合
    )),
    interval_days INTEGER DEFAULT 0,
    interval_hours INTEGER DEFAULT 0,
    month_day INTEGER DEFAULT 0,
    month INTEGER DEFAULT 0,
    day INTEGER DEFAULT 0,
    is_default INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('create', 'update', 'delete', 'import', 'export')),
    changed_fields TEXT DEFAULT '{}',
    timestamp DATETIME DEFAULT (datetime('now'))
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category_id);
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
CREATE INDEX IF NOT EXISTS idx_asset_field_values_asset ON asset_field_values(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_values_asset ON asset_values(asset_id);
CREATE INDEX IF NOT EXISTS idx_virtual_assets_category ON virtual_assets(category_id);
CREATE INDEX IF NOT EXISTS idx_virtual_assets_status ON virtual_assets(status);
CREATE INDEX IF NOT EXISTS idx_virtual_asset_field_values_asset ON virtual_asset_field_values(asset_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_category ON subscriptions(category_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_period ON subscriptions(period_id);
CREATE INDEX IF NOT EXISTS idx_sub_renewal_logs_sub ON sub_renewal_logs(subscription_id);
CREATE INDEX IF NOT EXISTS idx_sub_field_values_sub ON subscription_field_values(subscription_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_subscription_periods_rule_type ON subscription_periods(rule_type);

-- 记账模块
CREATE TABLE IF NOT EXISTS transaction_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    icon TEXT DEFAULT '',
    type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
    parent_id INTEGER REFERENCES transaction_categories(id) ON DELETE SET NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('cash', 'bank', 'wechat', 'alipay', 'credit', 'other')),
    balance REAL DEFAULT 0,
    icon TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK(type IN ('income', 'expense', 'transfer')),
    amount REAL NOT NULL CHECK(amount >= 0),
    category_id INTEGER REFERENCES transaction_categories(id) ON DELETE SET NULL,
    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    to_account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    transaction_date TEXT NOT NULL,
    merchant TEXT DEFAULT '',
    note TEXT DEFAULT '',
    source TEXT DEFAULT 'manual' CHECK(source IN ('manual', 'import_wechat', 'import_alipay')),
    original_id TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id);

-- 默认分类（不可删除）— type_id is set later by _migrate_unified_schema
INSERT OR IGNORE INTO categories (id, name, icon, sort_order)
    VALUES (1, '实体资产', '📦', 1);
INSERT OR IGNORE INTO virtual_categories (id, name, icon, description, sort_order)
    VALUES (1, '虚拟资产', '💻', '', 1);
INSERT OR IGNORE INTO subscription_categories (id, name, icon, description, sort_order)
    VALUES (1, '订阅', '🔄', '', 1);

-- 默认订阅周期配置（不可删除）
INSERT OR IGNORE INTO subscription_periods (name, rule_type, interval_days, interval_hours, month_day, month, day, is_default)
    VALUES ('日付', 'daily_interval', 1, 0, 0, 0, 0, 1);
INSERT OR IGNORE INTO subscription_periods (name, rule_type, interval_days, interval_hours, month_day, month, day, is_default)
    VALUES ('月付', 'monthly_day', 0, 0, 1, 0, 0, 1);
INSERT OR IGNORE INTO subscription_periods (name, rule_type, interval_days, interval_hours, month_day, month, day, is_default)
    VALUES ('季付', 'daily_interval', 90, 0, 0, 0, 0, 1);
INSERT OR IGNORE INTO subscription_periods (name, rule_type, interval_days, interval_hours, month_day, month, day, is_default)
    VALUES ('年付', 'yearly_date', 0, 0, 0, 1, 1, 1);
INSERT OR IGNORE INTO subscription_periods (name, rule_type, interval_days, interval_hours, month_day, month, day, is_default)
    VALUES ('两年付', 'daily_interval', 730, 0, 0, 0, 0, 1);
INSERT OR IGNORE INTO subscription_periods (name, rule_type, interval_days, interval_hours, month_day, month, day, is_default)
    VALUES ('三年付', 'daily_interval', 1095, 0, 0, 0, 0, 1);
INSERT OR IGNORE INTO subscription_periods (name, rule_type, interval_days, interval_hours, month_day, month, day, is_default)
    VALUES ('一次性', 'custom', 0, 0, 0, 0, 0, 1);
"""


_NEW_TABLES_SQL = """
-- 虚拟资产分类表
CREATE TABLE IF NOT EXISTS virtual_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER DEFAULT NULL REFERENCES virtual_categories(id) ON DELETE SET NULL,
    icon TEXT DEFAULT '',
    description TEXT DEFAULT '',
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- 虚拟资产自定义字段表
CREATE TABLE IF NOT EXISTS virtual_category_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES virtual_categories(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    field_type TEXT NOT NULL CHECK(field_type IN ('text', 'number', 'date', 'select', 'boolean')),
    required INTEGER DEFAULT 0,
    default_value TEXT DEFAULT '',
    options TEXT DEFAULT '{}',
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now'))
);

-- 虚拟资产表
CREATE TABLE IF NOT EXISTS virtual_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES virtual_categories(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    account_name TEXT DEFAULT '',
    password TEXT DEFAULT '',
    license_key TEXT DEFAULT '',
    expiry_date TEXT DEFAULT '',
    platform TEXT DEFAULT '',
    url TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'expired', 'cancelled')),
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- 虚拟资产自定义字段值表
CREATE TABLE IF NOT EXISTS virtual_asset_field_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL REFERENCES virtual_assets(id) ON DELETE CASCADE,
    field_id INTEGER NOT NULL REFERENCES virtual_category_fields(id) ON DELETE CASCADE,
    value TEXT DEFAULT '',
    UNIQUE(asset_id, field_id)
);

-- 订阅分类表
CREATE TABLE IF NOT EXISTS subscription_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    parent_id INTEGER DEFAULT NULL REFERENCES subscription_categories(id) ON DELETE SET NULL,
    icon TEXT DEFAULT '',
    description TEXT DEFAULT '',
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now'))
);

-- 订阅自定义字段表
CREATE TABLE IF NOT EXISTS subscription_category_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES subscription_categories(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    field_type TEXT NOT NULL CHECK(field_type IN ('text', 'number', 'date', 'select', 'boolean')),
    required INTEGER DEFAULT 0,
    default_value TEXT DEFAULT '',
    options TEXT DEFAULT '{}',
    sort_order INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT (datetime('now'))
);

-- 订阅自定义字段值表
CREATE TABLE IF NOT EXISTS subscription_field_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    field_id INTEGER NOT NULL REFERENCES subscription_category_fields(id) ON DELETE CASCADE,
    value TEXT DEFAULT '',
    UNIQUE(subscription_id, field_id)
);
"""


def _migrate_data(conn: sqlite3.Connection):
    """Migrate data from old shared categories table to new separate tables.

    This handles the case where the database was created with the old schema
    where categories table stored physical, virtual, and subscription categories
    with a 'type' field.
    """
    # Check if migration is needed by checking if old categories table has 'type' column
    cursor = conn.execute("PRAGMA table_info(categories)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'type' not in columns:
        # Already migrated or new database
        return

    logger.info("Detected old schema with shared categories table, migrating...")

    # Step 1: Create new tables first so we can insert data into them
    conn.executescript(_NEW_TABLES_SQL)

    # Step 2: Check if migration already done (virtual_categories has more than default)
    count = conn.execute("SELECT COUNT(*) FROM virtual_categories").fetchone()[0]
    if count > 1:
        logger.info("Migration already completed, skipping data migration")
        # Still need to drop and recreate old tables
        _recreate_old_tables(conn)
        return

    # Step 3: Migrate virtual categories (preserve IDs)
    conn.execute("""
        INSERT OR IGNORE INTO virtual_categories (id, name, parent_id, icon, description, sort_order, created_at, updated_at)
        SELECT id, name, parent_id, icon, description, sort_order, created_at, updated_at
        FROM categories WHERE type = 'virtual'
    """)

    # Step 4: Migrate subscription categories (preserve IDs)
    conn.execute("""
        INSERT OR IGNORE INTO subscription_categories (id, name, parent_id, icon, description, sort_order, created_at, updated_at)
        SELECT id, name, parent_id, icon, description, sort_order, created_at, updated_at
        FROM categories WHERE type = 'subscription'
    """)

    # Step 5: Ensure default categories exist in new tables
    conn.execute("""
        INSERT OR IGNORE INTO virtual_categories (id, name, icon, description, sort_order)
        VALUES (1, '虚拟资产', '💻', '', 1)
    """)
    conn.execute("""
        INSERT OR IGNORE INTO subscription_categories (id, name, icon, description, sort_order)
        VALUES (1, '订阅', '🔄', '', 1)
    """)

    # Step 6: Update subscription category_id to point to subscription_categories
    # Map old category IDs (type='subscription') to new subscription_categories IDs
    conn.execute("""
        UPDATE subscriptions
        SET category_id = (
            SELECT sc.id FROM subscription_categories sc
            WHERE sc.id = subscriptions.category_id
            LIMIT 1
        )
        WHERE category_id IN (SELECT id FROM categories WHERE type = 'subscription')
    """)

    # Step 7: Save physical categories data before dropping
    physical_cats = conn.execute("""
        SELECT id, name, parent_id, icon, description, sort_order, created_at, updated_at
        FROM categories WHERE type = 'physical'
    """).fetchall()

    # Save category_fields (they reference physical categories)
    cat_fields = conn.execute("SELECT * FROM category_fields").fetchall()

    # Save subscriptions data
    subs = conn.execute("SELECT * FROM subscriptions").fetchall()

    # Save other dependent data
    assets = conn.execute("SELECT * FROM assets").fetchall()
    asset_field_vals = conn.execute("SELECT * FROM asset_field_values").fetchall()
    asset_values = conn.execute("SELECT * FROM asset_values").fetchall()
    asset_attachments = conn.execute("SELECT * FROM asset_attachments").fetchall()
    sub_renewals = conn.execute("SELECT * FROM sub_renewal_logs").fetchall()

    # Step 8: Drop old tables that need to be recreated
    conn.execute("DROP TABLE IF EXISTS sub_renewal_logs")
    conn.execute("DROP TABLE IF EXISTS asset_attachments")
    conn.execute("DROP TABLE IF EXISTS asset_values")
    conn.execute("DROP TABLE IF EXISTS asset_field_values")
    conn.execute("DROP TABLE IF EXISTS assets")
    conn.execute("DROP TABLE IF EXISTS category_fields")
    conn.execute("DROP TABLE IF EXISTS subscriptions")
    conn.execute("DROP TABLE IF EXISTS categories")

    # Step 9: Recreate tables with new schema (via MIGRATION_SQL)
    conn.executescript(MIGRATION_SQL)

    # Step 10: Restore physical categories
    for cat in physical_cats:
        conn.execute("""
            INSERT OR IGNORE INTO categories (id, type_id, name, parent_id, icon, sort_order, created_at, updated_at)
            VALUES (?, 1, ?, ?, ?, ?, ?, ?)
        """, (cat[0], cat[1], cat[2], cat[3], cat[5], cat[6], cat[7]))

    # Step 11: Restore category_fields
    for field in cat_fields:
        conn.execute("""
            INSERT OR IGNORE INTO category_fields
            (id, category_id, field_name, field_type, required, default_value, options, sort_order, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(field))

    # Step 12: Restore assets
    for asset in assets:
        conn.execute("""
            INSERT OR IGNORE INTO assets
            (id, category_id, name, purchase_date, purchase_price, current_value, currency, notes, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(asset))

    # Step 13: Restore asset_field_values
    for afv in asset_field_vals:
        conn.execute("""
            INSERT OR IGNORE INTO asset_field_values (id, asset_id, category_field_id, value)
            VALUES (?, ?, ?, ?)
        """, tuple(afv))

    # Step 14: Restore asset_values
    for av in asset_values:
        conn.execute("""
            INSERT OR IGNORE INTO asset_values (id, asset_id, value, recorded_at, source, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, tuple(av))

    # Step 15: Restore asset_attachments
    for att in asset_attachments:
        conn.execute("""
            INSERT OR IGNORE INTO asset_attachments (id, asset_id, filename, filepath, mime_type, size, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tuple(att))

    # Step 16: Restore subscriptions
    for sub in subs:
        conn.execute("""
            INSERT OR IGNORE INTO subscriptions
            (id, category_id, name, amount, currency, cycle, start_date, next_renewal, auto_renew, reminder_days, notes, status, created_at, updated_at, period_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """, tuple(sub))

    # Step 17: Restore sub_renewal_logs
    for renewal in sub_renewals:
        conn.execute("""
            INSERT OR IGNORE INTO sub_renewal_logs (id, subscription_id, renewed_at, amount, method, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, tuple(renewal))

    conn.commit()
    logger.info("Migration complete")


def _recreate_old_tables(conn: sqlite3.Connection):
    """Recreate old tables without the type column (for when data migration is already done)."""
    # Check if categories still has 'type' column
    cursor = conn.execute("PRAGMA table_info(categories)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'type' not in columns:
        return

    # Save physical categories data
    physical_cats = conn.execute("""
        SELECT id, name, parent_id, icon, description, sort_order, created_at, updated_at
        FROM categories WHERE type = 'physical'
    """).fetchall()

    cat_fields = conn.execute("SELECT * FROM category_fields").fetchall()

    subs = conn.execute("SELECT * FROM subscriptions").fetchall()
    assets = conn.execute("SELECT * FROM assets").fetchall()
    asset_field_vals = conn.execute("SELECT * FROM asset_field_values").fetchall()
    asset_values = conn.execute("SELECT * FROM asset_values").fetchall()
    asset_attachments = conn.execute("SELECT * FROM asset_attachments").fetchall()
    sub_renewals = conn.execute("SELECT * FROM sub_renewal_logs").fetchall()

    # Drop old tables
    conn.execute("DROP TABLE IF EXISTS sub_renewal_logs")
    conn.execute("DROP TABLE IF EXISTS asset_attachments")
    conn.execute("DROP TABLE IF EXISTS asset_values")
    conn.execute("DROP TABLE IF EXISTS asset_field_values")
    conn.execute("DROP TABLE IF EXISTS assets")
    conn.execute("DROP TABLE IF EXISTS category_fields")
    conn.execute("DROP TABLE IF EXISTS subscriptions")
    conn.execute("DROP TABLE IF EXISTS categories")

    # Recreate with new schema
    conn.executescript(MIGRATION_SQL)

    # Restore data
    for cat in physical_cats:
        conn.execute("""
            INSERT OR IGNORE INTO categories (id, type_id, name, parent_id, icon, sort_order, created_at, updated_at)
            VALUES (?, 1, ?, ?, ?, ?, ?, ?)
        """, (cat[0], cat[1], cat[2], cat[3], cat[5], cat[6], cat[7]))

    for field in cat_fields:
        conn.execute("""
            INSERT OR IGNORE INTO category_fields
            (id, category_id, field_name, field_type, required, default_value, options, sort_order, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(field))

    for asset in assets:
        conn.execute("""
            INSERT OR IGNORE INTO assets
            (id, category_id, name, purchase_date, purchase_price, current_value, currency, notes, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(asset))

    for afv in asset_field_vals:
        conn.execute("""
            INSERT OR IGNORE INTO asset_field_values (id, asset_id, category_field_id, value)
            VALUES (?, ?, ?, ?)
        """, tuple(afv))

    for av in asset_values:
        conn.execute("""
            INSERT OR IGNORE INTO asset_values (id, asset_id, value, recorded_at, source, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, tuple(av))

    for att in asset_attachments:
        conn.execute("""
            INSERT OR IGNORE INTO asset_attachments (id, asset_id, filename, filepath, mime_type, size, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tuple(att))

    for sub in subs:
        conn.execute("""
            INSERT OR IGNORE INTO subscriptions
            (id, category_id, name, amount, currency, cycle, start_date, next_renewal, auto_renew, reminder_days, notes, status, created_at, updated_at, period_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """, tuple(sub))

    for renewal in sub_renewals:
        conn.execute("""
            INSERT OR IGNORE INTO sub_renewal_logs (id, subscription_id, renewed_at, amount, method, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, tuple(renewal))

    conn.commit()


# ---------------------------------------------------------------------------
# System asset-type field_config definitions
# ---------------------------------------------------------------------------
# These are the default custom fields for each system-preset asset type.
# Without them the asset form would only show a name field, which is useless.

_PHYSICAL_FIELD_CONFIG = json.dumps({
    "fields": [
        {"key": "purchase_date", "label": "购买日期", "type": "date", "required": False},
        {"key": "purchase_price", "label": "购买价格", "type": "number", "required": False,
         "options": {"min": 0, "prefix": "¥"}},
        {"key": "current_value", "label": "当前价值", "type": "number", "required": False,
         "options": {"min": 0, "prefix": "¥"}},
        {"key": "currency", "label": "货币", "type": "select", "required": False,
         "options": {"choices": [
             {"value": "CNY", "label": "CNY"},
             {"value": "USD", "label": "USD"},
             {"value": "EUR", "label": "EUR"},
         ]}},
        {"key": "notes", "label": "备注", "type": "textarea", "required": False,
         "options": {"rows": 3}},
    ]
}, ensure_ascii=False)

_VIRTUAL_FIELD_CONFIG = json.dumps({
    "fields": [
        {"key": "account_name", "label": "账号", "type": "text", "required": False},
        {"key": "password", "label": "密码", "type": "text", "required": False},
        {"key": "license_key", "label": "许可证号", "type": "text", "required": False},
        {"key": "expiry_date", "label": "到期日期", "type": "date", "required": False},
        {"key": "platform", "label": "平台", "type": "text", "required": False},
        {"key": "url", "label": "网址", "type": "text", "required": False},
        {"key": "notes", "label": "备注", "type": "textarea", "required": False,
         "options": {"rows": 3}},
    ]
}, ensure_ascii=False)

_SUBSCRIPTION_FIELD_CONFIG = json.dumps({
    "fields": [
        {"key": "amount", "label": "金额", "type": "number", "required": False,
         "options": {"min": 0, "prefix": "¥"}},
        {"key": "currency", "label": "货币", "type": "select", "required": False,
         "options": {"choices": [
             {"value": "CNY", "label": "CNY"},
             {"value": "USD", "label": "USD"},
             {"value": "EUR", "label": "EUR"},
         ]}},
        {"key": "cycle", "label": "周期", "type": "select", "required": False,
         "options": {"api_endpoint": "/subscription-periods/", "value_field": "id", "label_field": "name"}},
        {"key": "start_date", "label": "开始日期", "type": "date", "required": False},
        {"key": "next_renewal", "label": "下次续费", "type": "date", "required": False},
        {"key": "auto_renew", "label": "自动续费", "type": "boolean", "required": False},
        {"key": "reminder_days", "label": "提醒天数", "type": "number", "required": False,
         "options": {"min": 0, "max": 365}},
        {"key": "notes", "label": "备注", "type": "textarea", "required": False,
         "options": {"rows": 3}},
    ]
}, ensure_ascii=False)

_SYSTEM_TYPE_FIELDS = {
    1: _PHYSICAL_FIELD_CONFIG,
    2: _VIRTUAL_FIELD_CONFIG,
    3: _SUBSCRIPTION_FIELD_CONFIG,
}


def _ensure_system_type_field_config(conn: sqlite3.Connection) -> None:
    """Ensure system-preset asset types have the latest field_config.

    System types are always updated to the latest default configuration
    on startup, since they are managed by the system, not by users.
    """
    updated = False
    for type_id, field_config_json in _SYSTEM_TYPE_FIELDS.items():
        row = conn.execute(
            "SELECT field_config FROM asset_types WHERE id = ?", (type_id,)
        ).fetchone()
        if row is None:
            continue
        existing = row[0]
        # Always update system types to the latest config
        if existing != field_config_json:
            conn.execute(
                "UPDATE asset_types SET field_config = ? WHERE id = ?",
                (field_config_json, type_id),
            )
            updated = True
    if updated:
        conn.commit()
        logger.info("Updated system asset types with latest field_config")


def _migrate_unified_schema(conn: sqlite3.Connection):
    """Migrate to unified asset schema (asset_types + unified assets + categories.type_id).

    Handles three database states:
    1. Brand new DB — no tables yet → creates asset_types & assets, modifies categories
    2. Old schema assets table exists → renames to physical_assets, creates new tables
    3. Already migrated → no-op (asset_types already exists, old assets already renamed)
    """
    # Check if already fully migrated
    asset_types_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='asset_types'"
    ).fetchone() is not None

    old_assets_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='assets'"
    ).fetchone() is not None

    # If assets table exists, check if it already has the new schema (type_id column)
    assets_is_new = False
    if old_assets_exists:
        assets_cols = [
            row[1]
            for row in conn.execute("PRAGMA table_info(assets)").fetchall()
        ]
        assets_is_new = "type_id" in assets_cols

    if asset_types_exists and (not old_assets_exists or assets_is_new):
        # Check if categories already has type_id
        cat_cols = [
            row[1]
            for row in conn.execute("PRAGMA table_info(categories)").fetchall()
        ]
        if "type_id" in cat_cols:
            # Schema is fully migrated — but system types may still have empty
            # field_config from an earlier version.  Ensure they are populated.
            _ensure_system_type_field_config(conn)
            return  # Already fully migrated

    logger.info("Migrating to unified asset schema...")

    # --- Step 1: Handle old assets table (only if it has old schema) ---
    if old_assets_exists and not assets_is_new:
        # Drop tables that reference old assets table (will be recreated by MIGRATION_SQL)
        conn.execute("DROP TABLE IF EXISTS asset_field_values")
        conn.execute("DROP TABLE IF EXISTS asset_values")
        conn.execute("DROP TABLE IF EXISTS asset_attachments")
        # Rename old assets → physical_assets (preserve data)
        conn.execute("ALTER TABLE assets RENAME TO physical_assets")
        logger.info("Renamed old 'assets' → 'physical_assets'")

    # --- Step 2: Create asset_types table ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS asset_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            icon TEXT DEFAULT '',
            field_config JSON NOT NULL DEFAULT '{}',
            is_system INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT (datetime('now')),
            updated_at DATETIME DEFAULT (datetime('now'))
        )
    """)

    # --- Step 3: Create unified assets table ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_id INTEGER NOT NULL REFERENCES asset_types(id) ON DELETE RESTRICT,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            name TEXT NOT NULL,
            custom_data JSON,
            created_at DATETIME DEFAULT (datetime('now')),
            updated_at DATETIME DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_new_assets_type ON assets(type_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_new_assets_category ON assets(category_id)")

    # --- Step 4: Insert default system asset types with field_config ---
    # Uses module-level constants defined above.
    conn.execute(
        "INSERT OR IGNORE INTO asset_types (id, name, icon, field_config, is_system) "
        "VALUES (1, '实体资产', '📦', ?, 1)",
        (_PHYSICAL_FIELD_CONFIG,),
    )
    conn.execute(
        "INSERT OR IGNORE INTO asset_types (id, name, icon, field_config, is_system) "
        "VALUES (2, '虚拟资产', '💻', ?, 1)",
        (_VIRTUAL_FIELD_CONFIG,),
    )
    conn.execute(
        "INSERT OR IGNORE INTO asset_types (id, name, icon, field_config, is_system) "
        "VALUES (3, '订阅', '🔄', ?, 1)",
        (_SUBSCRIPTION_FIELD_CONFIG,),
    )

    # --- Step 5: Modify categories table to add type_id ---
    columns = [
        row[1]
        for row in conn.execute("PRAGMA table_info(categories)").fetchall()
    ]

    if "type_id" not in columns:
        # Save existing categories (handle both old and current column sets)
        cat_info = conn.execute("PRAGMA table_info(categories)").fetchall()
        cat_col_names = {row[1] for row in cat_info}

        # Build SELECT based on available columns
        select_cols = ["id", "name"]
        if "parent_id" in cat_col_names:
            select_cols.append("parent_id")
        if "icon" in cat_col_names:
            select_cols.append("icon")
        if "sort_order" in cat_col_names:
            select_cols.append("sort_order")
        if "created_at" in cat_col_names:
            select_cols.append("created_at")
        if "updated_at" in cat_col_names:
            select_cols.append("updated_at")

        existing_cats = conn.execute(
            f"SELECT {', '.join(select_cols)} FROM categories"
        ).fetchall()

        # Drop dependent tables
        conn.execute("DROP TABLE IF EXISTS category_fields")
        conn.execute("DROP TABLE IF EXISTS categories")

        # Recreate with type_id
        conn.execute("""
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_id INTEGER NOT NULL DEFAULT 1 REFERENCES asset_types(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                parent_id INTEGER DEFAULT NULL REFERENCES categories(id) ON DELETE SET NULL,
                icon TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT (datetime('now')),
                updated_at DATETIME DEFAULT (datetime('now'))
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_categories_type ON categories(type_id)"
        )

        # Restore data with type_id = 1, mapping columns safely
        for row in existing_cats:
            row_dict = dict(zip(select_cols, row))
            conn.execute(
                "INSERT INTO categories "
                "(id, type_id, name, parent_id, icon, sort_order, created_at, updated_at) "
                "VALUES (?, 1, ?, ?, ?, ?, ?, ?)",
                (
                    row_dict.get("id"),
                    row_dict.get("name", ""),
                    row_dict.get("parent_id"),
                    row_dict.get("icon", ""),
                    row_dict.get("sort_order", 0),
                    row_dict.get("created_at", ""),
                    row_dict.get("updated_at", ""),
                ),
            )

    # --- Step 6: Fix any categories rows that might have wrong type_id ---
    # (e.g. from MIGRATION_SQL INSERT OR IGNORE where description was mapped to type_id)
    conn.execute(
        "UPDATE categories SET type_id = 1 WHERE type_id IS NULL OR type_id = 0"
    )

    # --- Step 7: Recreate dependent tables that were dropped during migration ---
    # These tables are needed by the physical asset repos.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS category_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            field_name TEXT NOT NULL,
            field_type TEXT NOT NULL CHECK(field_type IN ('text', 'number', 'date', 'select', 'boolean')),
            required INTEGER DEFAULT 0,
            default_value TEXT DEFAULT '',
            options TEXT DEFAULT '{}',
            sort_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS asset_field_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            category_field_id INTEGER NOT NULL REFERENCES category_fields(id) ON DELETE CASCADE,
            value TEXT DEFAULT '',
            UNIQUE(asset_id, category_field_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS asset_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            value REAL NOT NULL DEFAULT 0,
            recorded_at DATETIME DEFAULT (datetime('now')),
            source TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS asset_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            mime_type TEXT DEFAULT '',
            size INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sub_renewal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id INTEGER NOT NULL,
            renewed_at DATETIME DEFAULT (datetime('now')),
            amount REAL NOT NULL DEFAULT 0,
            method TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )
    """)

    _ensure_system_type_field_config(conn)
    conn.commit()
    logger.info("Unified asset schema migration complete")


def _ensure_subscription_period_id(conn: sqlite3.Connection):
    """Ensure subscriptions table has the period_id column.

    For databases created with the full current MIGRATION_SQL the column is
    already present.  For older databases (where CREATE TABLE IF NOT EXISTS
    did NOT create a fresh table) we need to add the column explicitly.

    If the table does not exist yet (brand-new DB) this is a no-op —
    MIGRATION_SQL will create the table with the column included.
    """
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'"
        ).fetchall()
    }
    if "subscriptions" not in tables:
        return  # Will be created by MIGRATION_SQL

    columns = [
        row[1]
        for row in conn.execute("PRAGMA table_info(subscriptions)").fetchall()
    ]
    if "period_id" not in columns:
        conn.execute(
            "ALTER TABLE subscriptions "
            "ADD COLUMN period_id INTEGER REFERENCES subscription_periods(id)"
        )


def _migrate_subscription_periods(conn: sqlite3.Connection):
    """Migrate subscriptions.cycle to subscriptions.period_id.

    Maps old cycle enum values to the corresponding default
    subscription_periods rows.  The period_id column is guaranteed to exist
    because _ensure_subscription_period_id() runs first.
    """
    # Check whether any row still has a non-null cycle and a NULL period_id.
    has_unmigrated = conn.execute(
        "SELECT COUNT(*) FROM subscriptions "
        "WHERE cycle IS NOT NULL AND cycle != '' AND period_id IS NULL"
    ).fetchone()[0]

    if has_unmigrated == 0:
        return  # Nothing to migrate (or already migrated)

    logger.info("Migrating subscriptions.cycle → subscriptions.period_id ...")

    # cycle_value → period_name (default)
    CYCLE_TO_PERIOD_NAME = {
        "monthly": "月付",
        "quarterly": "季付",
        "yearly": "年付",
        "one_time": "一次性",
    }

    for cycle_value, period_name in CYCLE_TO_PERIOD_NAME.items():
        row = conn.execute(
            "SELECT id FROM subscription_periods WHERE name = ? AND is_default = 1",
            (period_name,),
        ).fetchone()
        if row:
            period_id = row[0]
            conn.execute(
                "UPDATE subscriptions SET period_id = ? WHERE cycle = ? AND period_id IS NULL",
                (period_id, cycle_value),
            )

    conn.commit()
    logger.info("Migration subscriptions.cycle → period_id complete")


def init_db(cfg: Config) -> sqlite3.Connection:
    global _db_instance
    os.makedirs(cfg.data_dir, exist_ok=True)
    db_path = Path(cfg.data_dir) / "asset-manager.db"
    logger.info(f"Opening database at {db_path}")

    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row

    # Run migration for old schema first
    _migrate_data(conn)

    # Ensure subscriptions.period_id column exists before MIGRATION_SQL runs
    # (MIGRATION_SQL only does CREATE TABLE IF NOT EXISTS, so on existing DBs
    # the column would not be added otherwise)
    _ensure_subscription_period_id(conn)

    # Then create all tables (IF NOT EXISTS ensures idempotency)
    conn.executescript(MIGRATION_SQL)

    # Migrate subscriptions.cycle → subscriptions.period_id
    _migrate_subscription_periods(conn)

    # Migrate to unified asset schema (asset_types, new assets, categories.type_id)
    _migrate_unified_schema(conn)

    logger.info("Migrations complete")

    # Initialise SQLAlchemy ORM engine (points at same .db file)
    from backend.app.orm_base import init_orm
    init_orm(db_path, shared_conn=conn)

    _db_instance = conn
    return conn


def get_db() -> sqlite3.Connection:
    if _db_instance is None:
        raise RuntimeError("Database not initialized. Call init_db first.")
    return _db_instance
