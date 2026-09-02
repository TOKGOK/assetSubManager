import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from './client'
import type {
  DashboardData, AuditLog, ListData,
  ImportResult, SqlImportResult,
  TransactionCategory, Account, Transaction, TransactionStats,
  CreateTransactionCategoryRequest, UpdateTransactionCategoryRequest,
  CreateAccountRequest, UpdateAccountRequest,
  CreateTransactionRequest, UpdateTransactionRequest,
  SubscriptionPeriod, CreateSubscriptionPeriodRequest, UpdateSubscriptionPeriodRequest,
} from '../types'

// ===== 订阅周期配置 =====
export function useSubscriptionPeriods() {
  return useQuery({
    queryKey: ['subscription-periods'],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: SubscriptionPeriod[] }>('/subscription-periods/')
      return data.data
    },
    staleTime: 5 * 60_000,
  })
}

export function useSubscriptionPeriod(id: number) {
  return useQuery({
    queryKey: ['subscription-period', id],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: SubscriptionPeriod }>(`/subscription-periods/${id}`)
      return data.data
    },
    enabled: id > 0,
  })
}

export function useCreateSubscriptionPeriod() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: CreateSubscriptionPeriodRequest) =>
      client.post('/subscription-periods/', req).then(r => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['subscription-periods'] })
    },
  })
}

export function useUpdateSubscriptionPeriod() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...req }: UpdateSubscriptionPeriodRequest & { id: number }) =>
      client.put(`/subscription-periods/${id}`, req).then(r => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['subscription-periods'] })
    },
  })
}

export function useDeleteSubscriptionPeriod() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => client.delete(`/subscription-periods/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['subscription-periods'] })
    },
  })
}

// ===== 仪表盘 =====
export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: DashboardData }>('/dashboard/')
      return data.data
    },
    staleTime: 60_000,
    retry: false,
  })
}

export function useCategoryStats() {
  return useQuery({
    queryKey: ['category-stats'],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: any[] }>('/dashboard/category-stats')
      return data.data
    },
    staleTime: 60_000,
    retry: false,
  })
}

// ===== 审计日志 =====
export function useAuditLogs(params?: { entity_type?: string; action?: string; page?: number; page_size?: number }) {
  return useQuery({
    queryKey: ['audit-logs', params],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: ListData<AuditLog> }>('/audit-log/', { params })
      return data.data
    },
  })
}

// ===== 导出 =====
function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function todayStr(): string {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}${m}${day}`
}

export function useExportCsv() {
  return useMutation({
    mutationFn: async () => {
      const resp = await client.get('/export/csv', { responseType: 'blob' })
      downloadBlob(resp.data, `assets_${todayStr()}.csv`)
    },
  })
}

export function useExportJson() {
  return useMutation({
    mutationFn: async () => {
      const resp = await client.get('/export/json', { responseType: 'blob' })
      downloadBlob(resp.data, `assets_${todayStr()}.json`)
    },
  })
}

export function useExportSql() {
  return useMutation({
    mutationFn: async () => {
      const resp = await client.get('/export/sql', { responseType: 'blob' })
      downloadBlob(resp.data, `backup_${todayStr()}.sql`)
    },
  })
}

// ===== 导入 =====
export function useImportCsv() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const resp = await client.post<{ code: number; data: ImportResult; message: string }>('/import/csv', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return resp.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['category-stats'] })
    },
  })
}

export function useImportJson() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const resp = await client.post<{ code: number; data: ImportResult; message: string }>('/import/json', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return resp.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['category-stats'] })
    },
  })
}

export function useImportSql() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const resp = await client.post<{ code: number; data: SqlImportResult; message: string }>('/import/sql', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return resp.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['categories'] })
      qc.invalidateQueries({ queryKey: ['category-stats'] })
    },
  })
}

// ===== 记账分类 =====
export function useTransactionCategories() {
  return useQuery({
    queryKey: ['transaction-categories'],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: TransactionCategory[] }>('/transaction-categories/')
      return data.data
    },
    staleTime: 5 * 60_000,
  })
}

export function useCreateTransactionCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: CreateTransactionCategoryRequest) =>
      client.post('/transaction-categories/', req).then(r => r.data.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['transaction-categories'] }),
  })
}

export function useUpdateTransactionCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...req }: UpdateTransactionCategoryRequest & { id: number }) =>
      client.put(`/transaction-categories/${id}`, req).then(r => r.data.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['transaction-categories'] }),
  })
}

export function useDeleteTransactionCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => client.delete(`/transaction-categories/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['transaction-categories'] }),
  })
}

// ===== 账户 =====
export function useAccounts(activeOnly = false) {
  return useQuery({
    queryKey: ['accounts', { activeOnly }],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: Account[] }>('/accounts/', {
        params: { active_only: activeOnly },
      })
      return data.data
    },
    staleTime: 5 * 60_000,
  })
}

export function useAccount(id: number) {
  return useQuery({
    queryKey: ['account', id],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: Account }>(`/accounts/${id}`)
      return data.data
    },
    enabled: id > 0,
  })
}

export function useCreateAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: CreateAccountRequest) =>
      client.post('/accounts/', req).then(r => r.data.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['accounts'] }),
  })
}

export function useUpdateAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...req }: UpdateAccountRequest & { id: number }) =>
      client.put(`/accounts/${id}`, req).then(r => r.data.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['accounts'] }),
  })
}

export function useDeleteAccount() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => client.delete(`/accounts/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['accounts'] }),
  })
}

// ===== 交易 =====
export function useTransactions(params?: {
  type?: string; category_id?: number; account_id?: number;
  date_from?: string; date_to?: string; search?: string;
  sort_by?: string; sort_order?: string; page?: number; page_size?: number
}) {
  return useQuery({
    queryKey: ['transactions', params],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: ListData<Transaction> }>('/transactions/', { params })
      return data.data
    },
    staleTime: 30_000,
  })
}

export function useTransaction(id: number) {
  return useQuery({
    queryKey: ['transaction', id],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: Transaction }>(`/transactions/${id}`)
      return data.data
    },
    enabled: id > 0,
  })
}

export function useCreateTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: CreateTransactionRequest) =>
      client.post('/transactions/', req).then(r => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export function useUpdateTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...req }: UpdateTransactionRequest & { id: number }) =>
      client.put(`/transactions/${id}`, req).then(r => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export function useDeleteTransaction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => client.delete(`/transactions/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export function useBatchDeleteTransactions() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ids: number[]) =>
      client.post('/transactions/batch-delete', { ids }).then(r => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: ['accounts'] })
    },
  })
}

export function useTransactionStats(params?: { date_from?: string; date_to?: string }) {
  return useQuery({
    queryKey: ['transaction-stats', params],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: TransactionStats }>('/transactions/stats', { params })
      return data.data
    },
    staleTime: 60_000,
  })
}

// ===== 账单导入 =====
export function useImportWechatBill() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ file, accountId }: { file: File; accountId?: number }) => {
      const form = new FormData()
      form.append('file', file)
      const params = accountId ? { account_id: accountId } : {}
      const resp = await client.post<{ code: number; data: ImportResult; message: string }>(
        '/transactions/import/wechat', form,
        { headers: { 'Content-Type': 'multipart/form-data' }, params }
      )
      return resp.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: ['transaction-stats'] })
    },
  })
}

export function useImportAlipayBill() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ file, accountId }: { file: File; accountId?: number }) => {
      const form = new FormData()
      form.append('file', file)
      const params = accountId ? { account_id: accountId } : {}
      const resp = await client.post<{ code: number; data: ImportResult; message: string }>(
        '/transactions/import/alipay', form,
        { headers: { 'Content-Type': 'multipart/form-data' }, params }
      )
      return resp.data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['transactions'] })
      qc.invalidateQueries({ queryKey: ['transaction-stats'] })
    },
  })
}
