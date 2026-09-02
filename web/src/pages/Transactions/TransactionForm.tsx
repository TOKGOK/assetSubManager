import { useEffect } from 'react'
import { Form, Input, InputNumber, Select, DatePicker, Radio, Button, message, Card } from 'antd'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import dayjs from 'dayjs'
import PageHeader from '../../components/layout/PageHeader'
import {
  useTransaction, useCreateTransaction, useUpdateTransaction,
  useTransactionCategories, useAccounts,
} from '../../api/hooks'
import type { CreateTransactionRequest } from '../../types'

export default function TransactionForm() {
  const { t } = useTranslation()
  const { id } = useParams()
  const isEdit = !!id
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const createTx = useCreateTransaction()
  const updateTx = useUpdateTransaction()
  const { data: existing } = useTransaction(isEdit ? Number(id) : 0)
  const { data: categories = [] } = useTransactionCategories()
  const { data: accounts = [] } = useAccounts()

  const watchedType = Form.useWatch('type', form) as string | undefined
  const filteredCategories = watchedType && watchedType !== 'transfer'
    ? categories.filter(c => c.type === watchedType)
    : categories

  useEffect(() => {
    if (isEdit && existing) {
      form.setFieldsValue({
        type: existing.type,
        amount: existing.amount,
        category_id: existing.category_id ?? undefined,
        account_id: existing.account_id ?? undefined,
        to_account_id: existing.to_account_id ?? undefined,
        transaction_date: existing.transaction_date ? dayjs(existing.transaction_date) : undefined,
        merchant: existing.merchant,
        note: existing.note,
      })
    }
  }, [isEdit, existing, form])

  async function handleSubmit(values: Record<string, any>) {
    const payload: CreateTransactionRequest = {
      type: values.type,
      amount: values.amount,
      transaction_date: values.transaction_date.format('YYYY-MM-DD HH:mm:ss'),
      merchant: values.merchant || '',
      note: values.note || '',
    }
    if (values.type !== 'transfer' && values.category_id) {
      payload.category_id = values.category_id
    }
    if (values.account_id) {
      payload.account_id = values.account_id
    }
    if (values.type === 'transfer' && values.to_account_id) {
      payload.to_account_id = values.to_account_id
    }

    if (isEdit) {
      await updateTx.mutateAsync({ id: Number(id), ...payload })
      message.success(t('transaction.transactionUpdated'))
    } else {
      await createTx.mutateAsync(payload)
      message.success(t('transaction.transactionCreated'))
    }
    navigate('/transactions')
  }

  return (
    <div>
      <PageHeader title={isEdit ? t('transaction.editTransaction') : t('transaction.addTransaction')} />
      <Card className="max-w-2xl">
        <Form form={form} layout="vertical" onFinish={handleSubmit} initialValues={{ type: 'expense' }}>
          <Form.Item name="type" label={t('transaction.type')} rules={[{ required: true }]}>
            <Radio.Group>
              <Radio.Button value="expense">{t('transaction.expense')}</Radio.Button>
              <Radio.Button value="income">{t('transaction.income')}</Radio.Button>
              <Radio.Button value="transfer">{t('transaction.transfer')}</Radio.Button>
            </Radio.Group>
          </Form.Item>

          <div className="flex gap-4">
            <Form.Item name="amount" label={t('transaction.amount')} rules={[{ required: true }]} className="flex-1">
              <InputNumber className="w-full" min={0} precision={2} prefix="¥" />
            </Form.Item>
            <Form.Item name="transaction_date" label={t('transaction.date')} rules={[{ required: true }]} className="flex-1">
              <DatePicker className="w-full" showTime format="YYYY-MM-DD HH:mm:ss" />
            </Form.Item>
          </div>

          {watchedType !== 'transfer' && (
            <Form.Item name="category_id" label={t('transaction.category')}>
              <Select
                placeholder={t('transaction.allCategories')}
                allowClear
                options={filteredCategories.map(c => ({ value: c.id, label: `${c.icon} ${c.name}` }))}
              />
            </Form.Item>
          )}

          <Form.Item name="account_id" label={t('transaction.account')}>
            <Select
              placeholder={t('transaction.allAccounts')}
              allowClear
              options={accounts.map(a => ({ value: a.id, label: a.name }))}
            />
          </Form.Item>

          {watchedType === 'transfer' && (
            <Form.Item name="to_account_id" label={t('transaction.toAccount')}>
              <Select
                placeholder={t('transaction.allAccounts')}
                allowClear
                options={accounts
                  .filter(a => a.id !== form.getFieldValue('account_id'))
                  .map(a => ({ value: a.id, label: a.name }))}
              />
            </Form.Item>
          )}

          <Form.Item name="merchant" label={t('transaction.merchant')}>
            <Input placeholder={t('transaction.merchant')} />
          </Form.Item>

          <Form.Item name="note" label={t('transaction.note')}>
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={createTx.isPending || updateTx.isPending}>
              {isEdit ? t('common.save') : t('transaction.addTransaction')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
