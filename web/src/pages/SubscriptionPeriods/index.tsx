import { useState } from 'react'
import { Table, Button, Space, Tag, Modal, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import PageHeader from '../../components/layout/PageHeader'
import { useSubscriptionPeriods, useDeleteSubscriptionPeriod } from '../../api/hooks'
import type { SubscriptionPeriod } from '../../types'
import PeriodForm from './PeriodForm'

export default function SubscriptionPeriods() {
  const { t } = useTranslation()
  const { data: periods, isLoading } = useSubscriptionPeriods()
  const deleteMutation = useDeleteSubscriptionPeriod()

  const [formVisible, setFormVisible] = useState(false)
  const [editingPeriod, setEditingPeriod] = useState<SubscriptionPeriod | null>(null)

  const handleDelete = (id: number, name: string, isDefault: boolean) => {
    if (isDefault) {
      message.warning(t('subscriptionPeriods.cannotDeleteDefault'))
      return
    }
    Modal.confirm({
      title: t('common.confirmDelete'),
      content: t('subscriptionPeriods.deleteConfirm', { name }),
      onOk: async () => {
        try {
          await deleteMutation.mutateAsync(id)
          message.success(t('common.deleted'))
        } catch { /* error handled by interceptor */ }
      },
    })
  }

  const columns = [
    {
      title: t('subscriptionPeriods.name'),
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: t('subscriptionPeriods.ruleType'),
      dataIndex: 'rule_type',
      key: 'rule_type',
      render: (type: string) => {
        const typeLabels: Record<string, string> = {
          daily_interval: t('subscriptionPeriods.ruleTypeDaily'),
          monthly_day: t('subscriptionPeriods.ruleTypeMonthly'),
          yearly_date: t('subscriptionPeriods.ruleTypeYearly'),
          custom: t('subscriptionPeriods.ruleTypeCustom'),
        }
        return <Tag>{typeLabels[type] || type}</Tag>
      },
    },
    {
      title: t('subscriptionPeriods.rule'),
      key: 'rule',
      render: (_: unknown, record: SubscriptionPeriod) => {
        if (record.rule_type === 'daily_interval') {
          return record.interval_days === 0
            ? t('subscriptionPeriods.oneTime')
            : t('subscriptionPeriods.everyNDays', { n: record.interval_days })
        }
        if (record.rule_type === 'monthly_day') {
          return t('subscriptionPeriods.everyMonthDay', { day: record.month_day })
        }
        if (record.rule_type === 'yearly_date') {
          return t('subscriptionPeriods.everyYearDate', { month: record.month, day: record.day })
        }
        if (record.rule_type === 'custom') {
          const parts: string[] = []
          if (record.interval_days > 0) parts.push(t('subscriptionPeriods.nDays', { n: record.interval_days }))
          if (record.interval_hours > 0) parts.push(t('subscriptionPeriods.nHours', { n: record.interval_hours }))
          return parts.length > 0 ? parts.join(' ') : t('subscriptionPeriods.oneTime')
        }
        return '-'
      },
    },
    {
      title: t('subscriptionPeriods.isDefault'),
      dataIndex: 'is_default',
      key: 'is_default',
      render: (isDefault: boolean) => (
        <Tag color={isDefault ? 'green' : 'default'}>
          {isDefault ? t('common.yes') : t('common.no')}
        </Tag>
      ),
    },
    {
      title: t('common.actions'),
      key: 'actions',
      render: (_: unknown, record: SubscriptionPeriod) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setEditingPeriod(record)
              setFormVisible(true)
            }}
          >
            {t('common.edit')}
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            disabled={record.is_default}
            onClick={() => handleDelete(record.id, record.name, record.is_default)}
          >
            {t('common.delete')}
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title={t('subscriptionPeriods.title')}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingPeriod(null)
              setFormVisible(true)
            }}
          >
            {t('common.create')}
          </Button>
        }
      />

      <Table
        columns={columns}
        dataSource={periods || []}
        rowKey="id"
        loading={isLoading}
      />

      {formVisible && (
        <PeriodForm
          period={editingPeriod}
          onClose={() => {
            setFormVisible(false)
            setEditingPeriod(null)
          }}
        />
      )}
    </div>
  )
}
