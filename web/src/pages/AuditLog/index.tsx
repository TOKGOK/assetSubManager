import { useState } from 'react'
import { Table, Tag, Select, Space } from 'antd'
import { useTranslation } from 'react-i18next'
import PageHeader from '../../components/layout/PageHeader'
import { useAuditLogs } from '../../api/hooks'

const actionColors: Record<string, string> = {
  create: 'green',
  update: 'blue',
  delete: 'red',
  import: 'purple',
  export: 'cyan',
}

export default function AuditLog() {
  const { t } = useTranslation()
  const [page, setPage] = useState(1)
  const [entityType, setEntityType] = useState('')
  const [action, setAction] = useState('')

  const { data, isLoading } = useAuditLogs({ page, entity_type: entityType, action })

  const actionLabels: Record<string, string> = {
    create: t('auditLog.create'),
    update: t('auditLog.update'),
    delete: t('auditLog.delete'),
    import: t('auditLog.import'),
    export: t('auditLog.export'),
  }

  const entityLabels: Record<string, string> = {
    asset: t('auditLog.asset'),
    category: t('auditLog.category'),
    subscription: t('auditLog.subscription'),
  }

  const columns = [
    { title: t('auditLog.time'), dataIndex: 'timestamp', key: 'timestamp', width: 180 },
    { title: t('auditLog.entity'), dataIndex: 'entity_type', key: 'entity_type',
      render: (text: string) => entityLabels[text] || text },
    { title: t('auditLog.entityId'), dataIndex: 'entity_id', key: 'entity_id', width: 60 },
    { title: t('auditLog.action'), dataIndex: 'action', key: 'action',
      render: (a: string) => <Tag color={actionColors[a]}>{actionLabels[a] || a}</Tag> },
    { title: t('auditLog.changedFields'), dataIndex: 'changed_fields', key: 'changed_fields',
      render: (v: string) => {
        try {
          const obj = JSON.parse(v)
          return Object.keys(obj).length > 0 ? Object.keys(obj).join(', ') : '-'
        } catch { return '-' }
      },
    },
  ]

  return (
    <div>
      <PageHeader title={t('auditLog.title')} />

      <Space className="mb-4">
        <Select
          placeholder={t('auditLog.entityTypePlaceholder')}
          allowClear
          className="w-36"
          value={entityType || undefined}
          onChange={v => { setEntityType(v || ''); setPage(1) }}
          options={[
            { value: 'asset', label: t('auditLog.asset') },
            { value: 'category', label: t('auditLog.category') },
            { value: 'subscription', label: t('auditLog.subscription') },
          ]}
        />
        <Select
          placeholder={t('auditLog.actionPlaceholder')}
          allowClear
          className="w-36"
          value={action || undefined}
          onChange={v => { setAction(v || ''); setPage(1) }}
          options={[
            { value: 'create', label: t('auditLog.create') },
            { value: 'update', label: t('auditLog.update') },
            { value: 'delete', label: t('auditLog.delete') },
          ]}
        />
      </Space>

      <Table
        dataSource={data?.items || []}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        virtual
        scroll={{ y: 600, x: 'max-content' }}
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
