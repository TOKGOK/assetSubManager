import { useState } from 'react'
import { Table, Button, Modal, Form, Input, InputNumber, Select, Popconfirm, Tag, Space, Tabs, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import PageHeader from '../../components/layout/PageHeader'
import {
  useTransactionCategories,
  useCreateTransactionCategory,
  useUpdateTransactionCategory,
  useDeleteTransactionCategory,
} from '../../api/hooks'
import type { TransactionCategory, CreateTransactionCategoryRequest } from '../../types'

export default function TransactionCategoriesPage() {
  const { t } = useTranslation()
  const { data: categories = [], isLoading } = useTransactionCategories()
  const createCategory = useCreateTransactionCategory()
  const updateCategory = useUpdateTransactionCategory()
  const deleteCategory = useDeleteTransactionCategory()

  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState<string>('all')
  const [form] = Form.useForm()

  function openCreateModal() {
    setEditingId(null)
    form.resetFields()
    form.setFieldsValue({ type: 'expense', sort_order: 0 })
    setModalOpen(true)
  }

  function openEditModal(category: TransactionCategory) {
    setEditingId(category.id)
    form.setFieldsValue({
      name: category.name,
      icon: category.icon,
      type: category.type,
      sort_order: category.sort_order,
    })
    setModalOpen(true)
  }

  async function handleSubmit(values: Record<string, any>) {
    if (editingId) {
      await updateCategory.mutateAsync({ id: editingId, ...values })
      message.success(t('common.success'))
    } else {
      await createCategory.mutateAsync(values as CreateTransactionCategoryRequest)
      message.success(t('common.success'))
    }
    setModalOpen(false)
    form.resetFields()
  }

  async function handleDelete(id: number) {
    await deleteCategory.mutateAsync(id)
    message.success(t('common.deleted'))
  }

  const filteredCategories = activeTab === 'all'
    ? categories
    : categories.filter((c) => c.type === activeTab)

  const columns = [
    {
      title: t('transactionCategory.icon'), dataIndex: 'icon', key: 'icon', width: 60,
      render: (icon: string) => <span className="text-lg">{icon || '-'}</span>,
    },
    {
      title: t('transactionCategory.name'), dataIndex: 'name', key: 'name',
    },
    {
      title: t('transactionCategory.type'), dataIndex: 'type', key: 'type',
      render: (type: string) => (
        <Tag color={type === 'income' ? 'green' : 'red'}>
          {type === 'income' ? t('transactionCategory.income') : t('transactionCategory.expense')}
        </Tag>
      ),
    },
    {
      title: t('transactionCategory.sortOrder', '排序'), dataIndex: 'sort_order', key: 'sort_order', align: 'right' as const,
    },
    {
      title: t('common.actions'), key: 'action', width: 150,
      render: (_: unknown, record: TransactionCategory) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)}>
            {t('common.edit')}
          </Button>
          <Popconfirm title={t('transactionCategory.deleteConfirm')} onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>{t('common.delete')}</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const typeOptions = [
    { value: 'expense', label: t('transactionCategory.expense') },
    { value: 'income', label: t('transactionCategory.income') },
  ]

  return (
    <div>
      <PageHeader
        title={t('transactionCategory.title')}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
            {t('transactionCategory.addCategory')}
          </Button>
        }
      />

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        className="mb-4"
        items={[
          { key: 'all', label: t('transactionCategory.all', '全部') },
          { key: 'expense', label: t('transactionCategory.expense') },
          { key: 'income', label: t('transactionCategory.income') },
        ]}
      />

      <Table
        dataSource={filteredCategories}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={false}
      />

      <Modal
        title={editingId ? t('transactionCategory.editCategory') : t('transactionCategory.addCategory')}
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={createCategory.isPending || updateCategory.isPending}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit} className="mt-4">
          <Form.Item name="name" label={t('transactionCategory.name')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="type" label={t('transactionCategory.type')} rules={[{ required: true }]}>
            <Select options={typeOptions} />
          </Form.Item>
          <Form.Item name="icon" label={t('transactionCategory.icon')}>
            <Input placeholder="emoji" />
          </Form.Item>
          <Form.Item name="sort_order" label={t('transactionCategory.sortOrder', '排序')} initialValue={0}>
            <InputNumber className="w-full" min={0} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
