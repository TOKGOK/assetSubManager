import { Form, Input, InputNumber, Select, Switch } from 'antd'
import { useTranslation } from 'react-i18next'
import type { CategoryField } from '../../types'

interface CustomFieldFormProps {
  fields: CategoryField[]
  /** 已填写的值（编辑模式） */
  values?: Record<number, string>
}

export default function CustomFieldForm({ fields, values }: CustomFieldFormProps) {
  const { t } = useTranslation()

  return (
    <>
      {fields.map((f) => {
        const name = ['custom_fields', String(f.id)]
        const rules = f.required ? [{ required: true, message: t('common.pleaseFillField', { name: f.field_name }) }] : []

        switch (f.field_type) {
          case 'text':
            return (
              <Form.Item key={f.id} name={name} label={f.field_name} rules={rules}>
                <Input defaultValue={values?.[f.id]} />
              </Form.Item>
            )
          case 'number':
            return (
              <Form.Item key={f.id} name={name} label={f.field_name} rules={rules}>
                <InputNumber className="w-full" defaultValue={values?.[f.id] ? Number(values[f.id]) : undefined} />
              </Form.Item>
            )
          case 'date':
            return (
              <Form.Item key={f.id} name={name} label={f.field_name} rules={rules}>
                <Input type="date" defaultValue={values?.[f.id]} />
              </Form.Item>
            )
          case 'select': {
            let options: string[] = []
            try {
              const parsed = JSON.parse(f.options || '{}')
              options = parsed.options || []
            } catch { /* ignore */ }
            return (
              <Form.Item key={f.id} name={name} label={f.field_name} rules={rules}>
                <Select
                  options={options.map((o: string) => ({ value: o, label: o }))}
                  placeholder={t('common.selectPlaceholder')}
                  allowClear
                />
              </Form.Item>
            )
          }
          case 'boolean':
            return (
              <Form.Item key={f.id} name={name} label={f.field_name} valuePropName="checked" rules={rules}>
                <Switch />
              </Form.Item>
            )
          default:
            return null
        }
      })}
    </>
  )
}
