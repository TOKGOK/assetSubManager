import { useEffect } from 'react'
import { Modal, Form, Input, Select, InputNumber, message } from 'antd'
import { useTranslation } from 'react-i18next'
import { useCreateSubscriptionPeriod, useUpdateSubscriptionPeriod } from '../../api/hooks'
import type { SubscriptionPeriod, CreateSubscriptionPeriodRequest } from '../../types'

interface PeriodFormProps {
  period: SubscriptionPeriod | null
  onClose: () => void
}

export default function PeriodForm({ period, onClose }: PeriodFormProps) {
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const createMutation = useCreateSubscriptionPeriod()
  const updateMutation = useUpdateSubscriptionPeriod()

  const ruleType = Form.useWatch('rule_type', form)

  useEffect(() => {
    if (period) {
      form.setFieldsValue({
        name: period.name,
        rule_type: period.rule_type,
        interval_days: period.interval_days,
        interval_hours: period.interval_hours,
        month_day: period.month_day,
        month: period.month,
        day: period.day,
      })
    } else {
      form.resetFields()
    }
  }, [period, form])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (period) {
        await updateMutation.mutateAsync({ id: period.id, ...values } as CreateSubscriptionPeriodRequest & { id: number })
        message.success(t('common.success'))
      } else {
        await createMutation.mutateAsync(values)
        message.success(t('common.success'))
      }
      onClose()
    } catch (error) {
      if (error instanceof Error) {
        message.error(error.message)
      }
    }
  }

  return (
    <Modal
      title={period ? t('subscriptionPeriods.editTitle') : t('subscriptionPeriods.createTitle')}
      open={true}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label={t('subscriptionPeriods.name')}
          rules={[{ required: true, message: t('common.required') }]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          name="rule_type"
          label={t('subscriptionPeriods.ruleType')}
          rules={[{ required: true, message: t('common.required') }]}
        >
          <Select>
            <Select.Option value="daily_interval">
              {t('subscriptionPeriods.ruleTypeDaily')}
            </Select.Option>
            <Select.Option value="monthly_day">
              {t('subscriptionPeriods.ruleTypeMonthly')}
            </Select.Option>
            <Select.Option value="yearly_date">
              {t('subscriptionPeriods.ruleTypeYearly')}
            </Select.Option>
            <Select.Option value="custom">
              {t('subscriptionPeriods.ruleTypeCustom')}
            </Select.Option>
          </Select>
        </Form.Item>

        {/* daily_interval */}
        {ruleType === 'daily_interval' && (
          <Form.Item
            name="interval_days"
            label={t('subscriptionPeriods.intervalDays')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        )}

        {/* monthly_day */}
        {ruleType === 'monthly_day' && (
          <Form.Item
            name="month_day"
            label={t('subscriptionPeriods.monthDay')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <InputNumber min={1} max={31} style={{ width: '100%' }} />
          </Form.Item>
        )}

        {/* yearly_date */}
        {ruleType === 'yearly_date' && (
          <>
            <Form.Item
              name="month"
              label={t('subscriptionPeriods.month')}
              rules={[{ required: true, message: t('common.required') }]}
            >
              <InputNumber min={1} max={12} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="day"
              label={t('subscriptionPeriods.day')}
              rules={[{ required: true, message: t('common.required') }]}
            >
              <InputNumber min={1} max={31} style={{ width: '100%' }} />
            </Form.Item>
          </>
        )}

        {/* custom */}
        {ruleType === 'custom' && (
          <>
            <Form.Item
              name="interval_days"
              label={t('subscriptionPeriods.intervalDays')}
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="interval_hours"
              label={t('subscriptionPeriods.intervalHours')}
            >
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
          </>
        )}
      </Form>
    </Modal>
  )
}
