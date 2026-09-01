import { useState, useMemo } from 'react'
import { Table, Button, Space, Tag, Input, Select, Popconfirm, message } from 'antd'
import { PlusOutlined, SearchOutlined, DeleteOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import PageHeader from '../../components/layout/PageHeader'
import { useAssets, useBatchDeleteAssets, useDeleteAsset } from '../../api/hooks/assets'
import { useAssetTypes } from '../../api/hooks/asset-types'
import { useCategoriesByType } from '../../api/hooks/categories'
import { useDebounce } from '../../hooks/useDebounce'
import type { Asset } from '../../types/asset'
import type { AssetType, FieldDefinition } from '../../types/asset-type'

export default function AssetManagement() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [selectedTypeIds, setSelectedTypeIds] = useState<number[]>([])
  const [page, setPage] = useState(1)
  const [searchInput, setSearchInput] = useState('')
  const debouncedSearch = useDebounce(searchInput, 300)
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [status, setStatus] = useState('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([])

  // Fetch asset types from API
  const { data: assetTypes = [] } = useAssetTypes()

  // Is single type selected?
  const isSingleType = selectedTypeIds.length === 1
  const singleTypeId = isSingleType ? selectedTypeIds[0] : null
  const singleTypeObj = singleTypeId ? assetTypes.find(at => at.id === singleTypeId) : null

  // Build API params
  const apiParams = useMemo(() => ({
    type_ids: selectedTypeIds.length > 0 ? selectedTypeIds.join(',') : undefined,
    category_id: categoryId,
    search: debouncedSearch || undefined,
    status: status || undefined,
    page,
  }), [selectedTypeIds, categoryId, debouncedSearch, status, page])

  // Unified assets query
  const { data: assetsData, isLoading } = useAssets(apiParams)

  // Categories by selected type (only when single type selected)
  const { data: categories = [] } = useCategoriesByType(singleTypeId ?? 0)

  // Mutations
  const batchDelete = useBatchDeleteAssets()
  const deleteAsset = useDeleteAsset()

  // Type map for quick lookup
  const typeMap = useMemo(() => {
    const map = new Map<number, AssetType>()
    assetTypes.forEach(at => map.set(at.id, at))
    return map
  }, [assetTypes])

  // Status options for filter
  const statusOptions = useMemo(() => [
    { value: 'active', label: t('assets.statusActive') },
    { value: 'sold', label: t('assets.statusSold') },
    { value: 'disposed', label: t('assets.statusDisposed') },
    { value: 'cancelled', label: t('subscriptions.statusCancelled') },
    { value: 'expired', label: t('subscriptions.statusExpired') },
  ], [t])

  // Status display map
  const statusMap: Record<string, { label: string; color: string }> = useMemo(() => ({
    active: { label: t('assets.statusActive'), color: 'green' },
    cancelled: { label: t('subscriptions.statusCancelled'), color: 'default' },
    expired: { label: t('subscriptions.statusExpired'), color: 'red' },
    sold: { label: t('assets.statusSold'), color: 'default' },
    disposed: { label: t('assets.statusDisposed'), color: 'red' },
  }), [t])

  // Render field value based on field type
  const renderFieldValue = (value: any, field: FieldDefinition): React.ReactNode => {
    if (value == null || value === '') return '-'
    switch (field.type) {
      case 'number': {
        const num = Number(value)
        if (isNaN(num)) return String(value)
        const prefix = field.options?.prefix || ''
        const suffix = field.options?.suffix || ''
        return `${prefix}${num.toLocaleString()}${suffix}`
      }
      case 'boolean':
        return value ? t('common.yes') : t('common.no')
      case 'date':
      case 'datetime':
        return String(value)
      case 'select': {
        const choice = field.options?.choices?.find(c => c.value === value)
        return choice ? choice.label : String(value)
      }
      default:
        return String(value)
    }
  }

  // Table columns
  const columns = useMemo(() => {
    // Base columns (always shown)
    const baseColumns: any[] = [
      {
        title: t('assetManagement.type'),
        key: 'type',
        width: 120,
        render: (_: unknown, record: Asset) => {
          const at = typeMap.get(record.type_id)
          return (
            <Tag color="blue">
              {at?.icon && <span className="mr-1">{at.icon}</span>}
              {at?.name || `Type ${record.type_id}`}
            </Tag>
          )
        },
      },
      {
        title: t('common.name'),
        dataIndex: 'name',
        key: 'name',
        render: (text: string, record: Asset) => (
          <a onClick={() => navigate(`/assets/${record.id}/edit`)}>{text}</a>
        ),
      },
      {
        title: t('common.category'),
        key: 'category',
        render: (_: unknown, record: Asset) => record.category?.name || '-',
      },
    ]

    // Single type mode: add dynamic columns from field_config
    if (isSingleType && singleTypeObj?.field_config?.fields) {
      const fields = singleTypeObj.field_config.fields
      const dynamicCols = fields.map((field) => ({
        title: field.label,
        key: `custom_${field.key}`,
        render: (_: unknown, record: Asset) => {
          const value = field.type === 'computed'
            ? record.computed_fields?.[field.key]
            : record.custom_data?.[field.key]
          return renderFieldValue(value, field)
        },
      }))

      return [
        ...baseColumns,
        ...dynamicCols,
        {
          title: t('common.status'),
          dataIndex: 'status',
          key: 'status',
          width: 100,
          render: (s: string) => s ? (
            <Tag color={statusMap[s]?.color}>{statusMap[s]?.label || s}</Tag>
          ) : '-',
        },
        {
          title: t('common.actions'),
          key: 'action',
          width: 150,
          render: (_: unknown, record: Asset) => (
            <Space>
              <Button type="link" size="small" onClick={() => navigate(`/assets/${record.id}/edit`)}>
                {t('common.edit')}
              </Button>
              <Popconfirm
                title={t('common.confirmDelete')}
                onConfirm={async () => {
                  await deleteAsset.mutateAsync(record.id)
                  message.success(t('common.deleted'))
                }}
              >
                <Button type="link" danger size="small">
                  {t('common.delete')}
                </Button>
              </Popconfirm>
            </Space>
          ),
        },
      ]
    }

    // Multi-type or all-types mode: show common columns only
    return [
      ...baseColumns,
      {
        title: t('common.status'),
        dataIndex: 'status',
        key: 'status',
        width: 100,
        render: (s: string) => s ? (
          <Tag color={statusMap[s]?.color}>{statusMap[s]?.label || s}</Tag>
        ) : '-',
      },
      {
        title: t('common.actions'),
        key: 'action',
        width: 150,
        render: (_: unknown, record: Asset) => (
          <Space>
            <Button type="link" size="small" onClick={() => navigate(`/assets/${record.id}/edit`)}>
              {t('common.edit')}
            </Button>
            <Popconfirm
              title={t('common.confirmDelete')}
              onConfirm={async () => {
                await deleteAsset.mutateAsync(record.id)
                message.success(t('common.deleted'))
              }}
            >
              <Button type="link" danger size="small">
                {t('common.delete')}
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ]
  }, [isSingleType, singleTypeObj, typeMap, t, navigate, deleteAsset, statusMap])

  // Row selection
  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: React.Key[]) => setSelectedRowKeys(keys),
  }

  // Batch delete handler
  const handleBatchDelete = async () => {
    try {
      await batchDelete.mutateAsync(selectedRowKeys as number[])
      setSelectedRowKeys([])
      message.success(t('common.deleted'))
    } catch {
      message.error(t('common.error'))
    }
  }

  // Type change handler - reset filters
  const handleTypeChange = (types: number[]) => {
    setSelectedTypeIds(types)
    setPage(1)
    setSearchInput('')
    setCategoryId(undefined)
    setStatus('')
    setSelectedRowKeys([])
  }

  // Build new asset URL: if single type selected, pass type_id
  const newAssetUrl = useMemo(() => {
    if (isSingleType && singleTypeId) {
      return `/assets/new?type_id=${singleTypeId}`
    }
    return '/assets/new'
  }, [isSingleType, singleTypeId])

  return (
    <div>
      <PageHeader title={t('nav.assetManagement')} />

      <Space className="mb-4" wrap>
        {/* Type filter - dynamic from API */}
        <Select
          mode="multiple"
          placeholder={t('assetManagement.filterByType')}
          value={selectedTypeIds}
          onChange={handleTypeChange}
          style={{ minWidth: 200 }}
          maxTagCount="responsive"
          allowClear
          options={assetTypes.map(at => ({
            value: at.id,
            label: at.icon ? `${at.icon} ${at.name}` : at.name,
          }))}
        />

        {/* Search - always enabled */}
        <Input
          placeholder={t('common.search')}
          prefix={<SearchOutlined />}
          value={searchInput}
          onChange={e => { setSearchInput(e.target.value); setPage(1) }}
          className="w-60"
          allowClear
        />

        {/* Category filter - only when single type selected */}
        <Select
          placeholder={t('assets.filterByCategory')}
          allowClear
          className="w-40"
          value={categoryId}
          onChange={v => { setCategoryId(v); setPage(1) }}
          options={categories.map(c => ({ value: c.id, label: c.name }))}
          disabled={!isSingleType || categories.length === 0}
        />

        {/* Status filter - always enabled */}
        <Select
          placeholder={t('assets.filterByStatus')}
          allowClear
          className="w-32"
          value={status || undefined}
          onChange={v => { setStatus(v || ''); setPage(1) }}
          options={statusOptions}
        />

        {/* Create button - always shown */}
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate(newAssetUrl)}
        >
          {t('common.create')}
        </Button>
      </Space>

      {/* Batch delete bar */}
      {selectedRowKeys.length > 0 && (
        <Space className="mb-4">
          <span>{t('common.selected', { count: selectedRowKeys.length })}</span>
          <Popconfirm
            title={t('common.confirmBatchDelete', { count: selectedRowKeys.length })}
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

      {/* Assets table */}
      <Table
        rowSelection={rowSelection}
        dataSource={assetsData?.items || []}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        virtual
        scroll={{ y: 600, x: 'max-content' }}
        pagination={{
          current: page,
          pageSize: assetsData?.page_size || 20,
          total: assetsData?.total || 0,
          onChange: setPage,
          showTotal: (total: number) => t('common.total', { count: total }),
        }}
      />
    </div>
  )
}
