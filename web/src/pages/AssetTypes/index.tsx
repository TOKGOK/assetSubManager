import { useState } from 'react'
import { Table, Button, Popconfirm, Space, Tag, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import PageHeader from '../../components/layout/PageHeader'
import { useAssetTypes, useDeleteAssetType } from '../../api/hooks/asset-types'
import type { AssetType } from '../../types/asset-type'
import TypeForm from './TypeForm'

export default function AssetTypes() {
  const { t } = useTranslation()
  const { data: types = [], isLoading } = useAssetTypes()
  const deleteMutation = useDeleteAssetType()

  const [formOpen, setFormOpen] = useState(false)
  const [editingType, setEditingType] = useState<AssetType | null>(null)

  const handleCreate = () => {
    setEditingType(null)
    setFormOpen(true)
  }

  const handleEdit = (record: AssetType) => {
    setEditingType(record)
    setFormOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id)
      message.success(t('common.deleted'))
    } catch {
      /* error handled by interceptor */
    }
  }

  const handleClose = () => {
    setFormOpen(false)
    setEditingType(null)
  }

  const columns = [
    {
      title: t('common.name'),
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: AssetType) => (
        <Space>
          {record.icon && <span>{record.icon}</span>}
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: t('assetTypes.systemPreset'),
      dataIndex: 'is_system',
      key: 'is_system',
      width: 120,
      render: (v: boolean) =>
        v ? <Tag color="blue">{t('assetTypes.yes')}</Tag> : <Tag>{t('assetTypes.no')}</Tag>,
    },
    {
      title: t('assetTypes.fieldCount'),
      key: 'fieldCount',
      width: 100,
      render: (_: unknown, record: AssetType) => record.field_config?.fields?.length || 0,
    },
    {
      title: t('common.actions'),
      key: 'actions',
      width: 150,
      render: (_: unknown, record: AssetType) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)}>
            {t('common.edit')}
          </Button>
          {record.is_system ? (
            <Button type="link" disabled size="small">
              {t('common.delete')}
            </Button>
          ) : (
            <Popconfirm title={t('common.confirmDelete')} onConfirm={() => handleDelete(record.id)}>
              <Button type="link" danger icon={<DeleteOutlined />} size="small">
                {t('common.delete')}
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title={t('nav.assetTypes')}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            {t('assetTypes.createTitle')}
          </Button>
        }
      />

      <Table
        dataSource={types}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={false}
      />

      {formOpen && <TypeForm assetType={editingType} onClose={handleClose} />}
    </div>
  )
}
