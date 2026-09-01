// ===== 通用 =====
export interface ApiResponse<T> {
  code: number
  data: T
  message: string
}

export interface ListData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// ===== 分类 =====
export interface Category {
  id: number
  name: string
  parent_id: number | null
  type_id: number
  icon: string
  description: string
  sort_order: number
  is_default?: boolean
  created_at: string
  updated_at: string
  children?: Category[]
  fields?: CategoryField[]
}

export interface CategoryField {
  id: number
  category_id: number
  field_name: string
  field_type: 'text' | 'number' | 'date' | 'select' | 'boolean'
  required: boolean
  default_value: string
  options: string // JSON string
  sort_order: number
  created_at: string
}

export interface CreateCategoryRequest {
  name: string
  parent_id?: number | null
  icon?: string
  description?: string
}

export interface UpdateCategoryRequest {
  name?: string
  parent_id?: number | null
  icon?: string
  description?: string
  sort_order?: number
}

// ===== 订阅周期配置 =====
export interface SubscriptionPeriod {
  id: number
  name: string
  rule_type: 'daily_interval' | 'monthly_day' | 'yearly_date' | 'custom'
  interval_days: number
  interval_hours: number
  month_day: number
  month: number
  day: number
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface CreateSubscriptionPeriodRequest {
  name: string
  rule_type: 'daily_interval' | 'monthly_day' | 'yearly_date' | 'custom'
  interval_days?: number
  interval_hours?: number
  month_day?: number
  month?: number
  day?: number
}

export interface UpdateSubscriptionPeriodRequest {
  name?: string
  rule_type?: 'daily_interval' | 'monthly_day' | 'yearly_date' | 'custom'
  interval_days?: number
  interval_hours?: number
  month_day?: number
  month?: number
  day?: number
}

// ===== 仪表盘 =====
export interface SubscriptionSummary {
  id: number
  name: string
  amount: number
  currency: string
  next_renewal: string
  status: string
  category_name?: string
}

export interface DashboardData {
  total_value: number
  total_count: number
  status_counts: Record<string, number>
  monthly_subscription: number
  upcoming_subscriptions: SubscriptionSummary[]
}

export interface CategoryStat {
  name: string
  count: number
  total_value: number
}

// ===== 导入结果 =====
export interface ImportResult {
  created: number
  skipped: number
  errors: string[]
}

export interface SqlImportResult {
  success: boolean
  errors: string[]
}

// ===== 审计日志 =====
export interface AuditLog {
  id: number
  entity_type: string
  entity_id: number
  action: string
  changed_fields: string
  timestamp: string
}

// ===== 记账模块 =====
export interface TransactionCategory {
  id: number
  name: string
  icon: string
  type: 'income' | 'expense'
  parent_id: number | null
  sort_order: number
}

export interface CreateTransactionCategoryRequest {
  name: string
  icon?: string
  type: 'income' | 'expense'
  parent_id?: number
  sort_order?: number
}

export interface UpdateTransactionCategoryRequest {
  name?: string
  icon?: string
  sort_order?: number
}

export interface Account {
  id: number
  name: string
  type: 'cash' | 'bank' | 'wechat' | 'alipay' | 'credit' | 'other'
  balance: number
  icon: string
  notes: string
  sort_order: number
  is_active: boolean
}

export interface CreateAccountRequest {
  name: string
  type: string
  balance?: number
  icon?: string
  notes?: string
  sort_order?: number
}

export interface UpdateAccountRequest {
  name?: string
  type?: string
  balance?: number
  icon?: string
  notes?: string
  sort_order?: number
  is_active?: boolean
}

export interface Transaction {
  id: number
  type: 'income' | 'expense' | 'transfer'
  amount: number
  category_id: number | null
  account_id: number | null
  to_account_id: number | null
  transaction_date: string
  merchant: string
  note: string
  source: 'manual' | 'import_wechat' | 'import_alipay'
  original_id: string
  created_at: string
  updated_at: string
  // Joined fields
  category_name: string
  category_icon: string
  account_name: string
}

export interface CreateTransactionRequest {
  type: 'income' | 'expense' | 'transfer'
  amount: number
  category_id?: number
  account_id?: number
  to_account_id?: number
  transaction_date: string
  merchant?: string
  note?: string
}

export interface UpdateTransactionRequest {
  type?: 'income' | 'expense' | 'transfer'
  amount?: number
  category_id?: number
  account_id?: number
  to_account_id?: number
  transaction_date?: string
  merchant?: string
  note?: string
}

export interface TransactionStats {
  total_income: number
  total_expense: number
  balance: number
  transaction_count: number
  category_breakdown: Array<{
    category_id: number
    category_name: string
    category_icon: string
    type: string
    total_amount: number
    count: number
  }>
}
