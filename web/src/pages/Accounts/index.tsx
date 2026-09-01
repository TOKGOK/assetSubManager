import { useState } from 'react'
import { Table, Button, Modal, Form, Input, InputNumber, Select, Popconfirm, Tag, Space, message } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import PageHeader from '../../components/layout/PageHeader'
import { useAccounts, useCreateAccount, useUpdateAccount, useDeleteAccount } from '../../api/hooks'
import type { Account, CreateAccountRequest } from '../../types'

const typeColorMap: Record<string, string> = {
  cash: 'green',
  bank: 'blue',
  wechat: 'green',
  alipay: 'blue',
  credit: 'orange',
  other: 'default',
}

function formatBalance(v: number): string {
  return `¥${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export default function AccountsPage() {
  const { t } = useTranslation()
  const { data: accounts = [], isLoading } = useAccounts()
  const createAccount = useCreateAccount()
  const updateAccount = useUpdateAccount()
  const deleteAccount = useDeleteAccount()

  const [modalOpen, setModalOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  const accountTypeOptions = [
    { value: 'cash', label: t('account.typeCash') },
    { value: 'bank', label: t('account.typeBank') },
    { value: 'wechat', label: t('account.typeWechat') },
    { value: 'alipay', label: t('account.typeAlipay') },
    { value: 'credit', label: t('account.typeCredit') },
    { value: 'other', label: t('account.typeOther') },
  ]

  function openCreateModal() {
    setEditingId(null)
    form.resetFields()
    form.setFieldsValue({ type: 'bank', balance: 0 })
    setModalOpen(true)
  }

  function openEditModal(account: Account) {
    setEditingId(account.id)
    form.setFieldsValue({
      name: account.name,
      type: account.type,
      balance: account.balance,
      icon: account.icon,
      notes: account.notes,
    })
    setModalOpen(true)
  }

  async function handleSubmit(values: Record<string, any>) {
    if (editingId) {
      await updateAccount.mutateAsync({ id: editingId, ...values })
      message.success(t('account.accountUpdated'))
    } else {
      await createAccount.mutateAsync(values as CreateAccountRequest)
      message.success(t('account.accountCreated'))
    }
    setModalOpen(false)
    form.resetFields()
  }

  async function handleDelete(id: number) {
    await deleteAccount.mutateAsync(id)
    message.success(t('account.accountDeleted'))
  }

  const typeLabelMap: Record<string, string> = {
    cash: t('account.typeCash'),
    bank: t('account.typeBank'),
    wechat: t('account.typeWechat'),
    alipay: t('account.typeAlipay'),
    credit: t('account.typeCredit'),
    other: t('account.typeOther'),
  }

  const columns = [
    {
      title: t('account.name'), dataIndex: 'name', key: 'name',
      render: (text: string, r: Account) => (
        <span>{r.icon ? `${r.icon} ` : ''}{text}</span>
      ),
    },
    {
      title: t('account.type'), dataIndex: 'type', key: 'type',
      render: (type: string) => (
        <Tag color={typeColorMap[type]}>{typeLabelMap[type] || type}</Tag>
      ),
    },
    {
      title: t('account.balance'), dataIndex: 'balance', key: 'balance', align: 'right' as const,
      render: (v: number) => formatBalance(v),
    },
    {
      title: t('account.notes'), dataIndex: 'notes', key: 'notes', ellipsis: true,
      render: (v: string) => v || '-',
    },
    {
      title: t('common.actions'), key: 'action', width: 150,
      render: (_: unknown, record: Account) => (
        <Space>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)}>
            {t('common.edit')}
          </Button>
          <Popconfirm title={t('account.deleteConfirm')} onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>{t('common.delete')}</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title={t('account.title')}
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
            {t('account.addAccount')}
          </Button>
        }
      />

      <Table
        dataSource={accounts}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={false}
      />

      <Modal
        title={editingId ? t('account.editAccount') : t('account.addAccount')}
        open={modalOpen}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        onOk={() => form.submit()}
        confirmLoading={createAccount.isPending || updateAccount.isPending}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit} className="mt-4">
          <Form.Item name="name" label={t('account.name')} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="type" label={t('account.type')} rules={[{ required: true }]}>
            <Select options={accountTypeOptions} />
          </Form.Item>
          <Form.Item name="balance" label={t('account.balance')} initialValue={0}>
            <InputNumber className="w-full" precision={2} prefix="¥" />
          </Form.Item>
          <Form.Item name="icon" label={t('account.icon')}>
            <Input placeholder="emoji" />
          </Form.Item>
          <Form.Item name="notes" label={t('account.notes')}>
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
