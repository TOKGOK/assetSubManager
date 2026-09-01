import { useState } from 'react'
import { Table, Button, Space, Tag, Popconfirm, message, DatePicker, Select, Input, Card, Statistic, Row, Col } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import PageHeader from '../../components/layout/PageHeader'
import {
  useTransactions, useDeleteTransaction, useBatchDeleteTransactions,
  useTransactionStats, useTransactionCategories, useAccounts,
} from '../../api/hooks'
import { useDebounce } from '../../hooks/useDebounce'
import type { Transaction } from '../../types'

export default function TransactionList() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  // Filters
  const [page, setPage] = useState(1)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().startOf('month'),
    dayjs().endOf('month'),
  ])
  const [typeFilter, setTypeFilter] = useState<string | undefined>()
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [accountId, setAccountId] = useState<number | undefined>()
  const [searchInput, setSearchInput] = useState('')
  const debouncedSearch = useDebounce(searchInput, 300)
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])

  // Build query params
  const params: Record<string, any> = { page }
  if (dateRange) {
    params.date_from = dateRange[0].format('YYYY-MM-DD')
    params.date_to = dateRange[1].format('YYYY-MM-DD')
  }
  if (typeFilter) params.type = typeFilter
  if (categoryId) params.category_id = categoryId
  if (accountId) params.account_id = accountId
  if (debouncedSearch) params.search = debouncedSearch

  const { data, isLoading } = useTransactions(params)
  const { data: stats } = useTransactionStats(
    dateRange ? { date_from: dateRange[0].format('YYYY-MM-DD'), date_to: dateRange[1].format('YYYY-MM-DD') } : undefined,
  )
  const { data: categories = [] } = useTransactionCategories()
  const { data: accounts = [] } = useAccounts()
  const deleteTx = useDeleteTransaction()
  const batchDelete = useBatchDeleteTransactions()

  const typeColorMap: Record<string, string> = {
    income: 'green',
    expense: 'red',
    transfer: 'blue',
  }

  const sourceMap: Record<string, string> = {
    manual: t('transaction.sourceManual'),
    import_wechat: t('transaction.sourceWechat'),
    import_alipay: t('transaction.sourceAlipay'),
  }

  const columns = [
    {
      title: t('transaction.date'), dataIndex: 'transaction_date', key: 'transaction_date', width: 110,
      render: (v: string) => v || '-',
    },
    {
      title: t('transaction.type'), dataIndex: 'type', key: 'type', width: 80,
      render: (type: string) => (
        <Tag color={typeColorMap[type]}>{t(`transaction.${type}`)}</Tag>
      ),
    },
    {
      title: t('transaction.category'), dataIndex: 'category_name', key: 'category_name', width: 100,
      render: (v: string, r: Transaction) => v ? <span>{r.category_icon} {v}</span> : '-',
    },
    {
      title: t('transaction.merchant'), dataIndex: 'merchant', key: 'merchant', ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: t('transaction.note'), dataIndex: 'note', key: 'note', ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: t('transaction.amount'), dataIndex: 'amount', key: 'amount', width: 130, align: 'right' as const,
      render: (v: number, r: Transaction) => {
        const formatted = `¥${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
        if (r.type === 'income') return <span style={{ color: '#52c41a' }}>+{formatted}</span>
        if (r.type === 'expense') return <span style={{ color: '#ff4d4f' }}>-{formatted}</span>
        return <span style={{ color: '#1890ff' }}>{formatted}</span>
      },
    },
    {
      title: t('transaction.account'), dataIndex: 'account_name', key: 'account_name', width: 100,
      render: (v: string) => v || '-',
    },
    {
      title: t('transaction.source'), dataIndex: 'source', key: 'source', width: 100,
      render: (v: string) => sourceMap[v] || v,
    },
    {
      title: t('common.actions'), key: 'action', width: 120,
      render: (_: unknown, record: Transaction) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => navigate(`/transactions/${record.id}/edit`)}>
            {t('common.edit')}
          </Button>
          <Popconfirm title={t('transaction.deleteConfirm')} onConfirm={async () => {
            await deleteTx.mutateAsync(record.id)
            message.success(t('common.deleted'))
          }}>
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>{t('common.delete')}</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
  }

  async function handleBatchDelete() {
    await batchDelete.mutateAsync(selectedRowKeys as number[])
    setSelectedRowKeys([])
    message.success(t('common.deleted'))
  }

  return (
    <div>
      <PageHeader
        title={t('transaction.title')}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/transactions/new')}>
            {t('transaction.addTransaction')}
          </Button>
        }
      />

      {/* Stats cards */}
      <Row gutter={16} className="mb-4">
        <Col span={6}>
          <Card>
            <Statistic
              title={t('transaction.totalIncome')}
              value={stats?.total_income ?? 0}
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={t('transaction.totalExpense')}
              value={stats?.total_expense ?? 0}
              precision={2}
              prefix="¥"
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={t('transaction.balance')}
              value={stats?.balance ?? 0}
              precision={2}
              prefix="¥"
              valueStyle={{ color: (stats?.balance ?? 0) >= 0 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={t('transaction.count')}
              value={stats?.transaction_count ?? 0}
              suffix={t('transaction.unitSuffix')}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Space className="mb-4" wrap>
        <DatePicker.RangePicker
          value={dateRange}
          onChange={(dates) => {
            setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null as any)
            setPage(1)
          }}
          allowClear
        />
        <Select
          placeholder={t('transaction.allTypes')}
          allowClear
          className="w-32"
          value={typeFilter}
          onChange={v => { setTypeFilter(v); setPage(1) }}
          options={[
            { value: 'income', label: t('transaction.income') },
            { value: 'expense', label: t('transaction.expense') },
            { value: 'transfer', label: t('transaction.transfer') },
          ]}
        />
        <Select
          placeholder={t('transaction.allCategories')}
          allowClear
          className="w-40"
          value={categoryId}
          onChange={v => { setCategoryId(v); setPage(1) }}
          options={categories.map(c => ({ value: c.id, label: `${c.icon} ${c.name}` }))}
        />
        <Select
          placeholder={t('transaction.allAccounts')}
          allowClear
          className="w-40"
          value={accountId}
          onChange={v => { setAccountId(v); setPage(1) }}
          options={accounts.map(a => ({ value: a.id, label: a.name }))}
        />
        <Input
          placeholder={t('transaction.searchPlaceholder')}
          value={searchInput}
          onChange={e => setSearchInput(e.target.value)}
          className="w-52"
          allowClear
        />
      </Space>

      {/* Batch delete bar */}
      {selectedRowKeys.length > 0 && (
        <Space className="mb-4">
          <span>{t('common.selected', { count: selectedRowKeys.length })}</span>
          <Popconfirm
            title={t('transaction.batchDeleteConfirm', { count: selectedRowKeys.length })}
            onConfirm={handleBatchDelete}
          >
            <Button danger icon={<DeleteOutlined />}>
              {t('common.batchDelete')}
            </Button>
          </Popconfirm>
          <Button onClick={() => setSelectedRowKeys([])}>
            {t('common.cancelSelection')}
          </Button>
        </Space>
      )}

      <Table
        rowSelection={rowSelection}
        dataSource={data?.items || []}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        scroll={{ x: 'max-content' }}
        pagination={{
          current: page,
          pageSize: data?.page_size || 20,
          total: data?.total || 0,
          onChange: setPage,
          showTotal: (total) => t('common.total', { count: total }),
        }}
      />
    </div>
  )
}
