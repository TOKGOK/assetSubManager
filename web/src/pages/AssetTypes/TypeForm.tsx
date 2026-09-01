import { useEffect, useState } from 'react'
import { Modal, Form, Input, Button, Card, Select, InputNumber, Switch, Space, message } from 'antd'
import { PlusOutlined, DeleteOutlined, UpOutlined, DownOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { useCreateAssetType, useUpdateAssetType, useAssetTypes } from '../../api/hooks/asset-types'
import type { AssetType, FieldType, FieldDefinition, FieldOptions } from '../../types/asset-type'

interface TypeFormProps {
  assetType: AssetType | null
  onClose: () => void
}

const FIELD_TYPES: { value: FieldType; label: string }[] = [
  { value: 'text', label: 'text' },
  { value: 'number', label: 'number' },
  { value: 'boolean', label: 'boolean' },
  { value: 'date', label: 'date' },
  { value: 'datetime', label: 'datetime' },
  { value: 'select', label: 'select' },
  { value: 'textarea', label: 'textarea' },
  { value: 'relation', label: 'relation' },
  { value: 'computed', label: 'computed' },
]

export default function TypeForm({ assetType, onClose }: TypeFormProps) {
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const createMutation = useCreateAssetType()
  const updateMutation = useUpdateAssetType()
  const { data: allTypes } = useAssetTypes()
  const [fields, setFields] = useState<FieldDefinition[]>([])

  useEffect(() => {
    if (assetType) {
      form.setFieldsValue({
        name: assetType.name,
        icon: assetType.icon || '',
      })
      setFields(assetType.field_config?.fields || [])
    } else {
      form.resetFields()
      setFields([])
    }
  }, [assetType, form])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      // Validate fields
      if (fields.length === 0) {
        message.error(t('assetTypes.fieldsRequired'))
        return
      }

      // Validate field keys uniqueness
      const keys = fields.map(f => f.key)
      const uniqueKeys = new Set(keys)
      if (keys.length !== uniqueKeys.size) {
        message.error(t('assetTypes.duplicateFieldKey'))
        return
      }

      // Validate each field
      for (const field of fields) {
        if (!field.key || !field.label || !field.type) {
          message.error(t('assetTypes.fieldIncomplete'))
          return
        }
      }

      const fieldConfig = { fields }

      if (assetType) {
        await updateMutation.mutateAsync({ id: assetType.id, name: values.name, icon: values.icon, field_config: fieldConfig })
        message.success(t('common.success'))
      } else {
        await createMutation.mutateAsync({ name: values.name, icon: values.icon, field_config: fieldConfig })
        message.success(t('common.success'))
      }
      onClose()
    } catch (error) {
      if (error instanceof Error) {
        message.error(error.message)
      }
    }
  }

  const addField = () => {
    setFields([...fields, { key: '', label: '', type: 'text', required: false, options: {} }])
  }

  const removeField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index))
  }

  const moveField = (index: number, direction: 'up' | 'down') => {
    const newFields = [...fields]
    const targetIndex = direction === 'up' ? index - 1 : index + 1
    if (targetIndex < 0 || targetIndex >= fields.length) return
    ;[newFields[index], newFields[targetIndex]] = [newFields[targetIndex], newFields[index]]
    setFields(newFields)
  }

  const updateField = (index: number, updates: Partial<FieldDefinition>) => {
    const newFields = [...fields]
    newFields[index] = { ...newFields[index], ...updates }
    setFields(newFields)
  }

  const updateFieldOptions = (index: number, updates: Partial<FieldOptions>) => {
    const newFields = [...fields]
    newFields[index] = { ...newFields[index], options: { ...newFields[index].options, ...updates } }
    setFields(newFields)
  }

  return (
    <Modal
      title={assetType ? t('assetTypes.editTitle') : t('assetTypes.createTitle')}
      open={true}
      onOk={handleSubmit}
      onCancel={onClose}
      width={800}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label={t('assetTypes.name')}
          rules={[{ required: true, message: t('common.required') }]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          name="icon"
          label={t('assetTypes.icon')}
        >
          <Input placeholder={t('assetTypes.iconPlaceholder')} />
        </Form.Item>
      </Form>

      <div className="mb-2 font-medium">{t('assetTypes.fieldConfig')}</div>

      <div className="space-y-3">
        {fields.map((field, index) => (
          <Card key={index} size="small" className="relative">
            <div className="grid grid-cols-2 gap-2 mb-2">
              <div>
                <label className="text-xs text-gray-500">{t('assetTypes.fieldKey')}</label>
                <Input
                  value={field.key}
                  onChange={e => updateField(index, { key: e.target.value })}
                  placeholder={t('assetTypes.fieldKeyPlaceholder')}
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">{t('assetTypes.fieldLabel')}</label>
                <Input
                  value={field.label}
                  onChange={e => updateField(index, { label: e.target.value })}
                  placeholder={t('assetTypes.fieldLabelPlaceholder')}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 mb-2">
              <div>
                <label className="text-xs text-gray-500">{t('assetTypes.fieldType')}</label>
                <Select
                  value={field.type}
                  onChange={v => updateField(index, { type: v })}
                  className="w-full"
                >
                  {FIELD_TYPES.map(ft => (
                    <Select.Option key={ft.value} value={ft.value}>
                      {t(`assetTypes.fieldType_${ft.value}`)}
                    </Select.Option>
                  ))}
                </Select>
              </div>
              <div className="flex items-end">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">{t('assetTypes.required')}</span>
                  <Switch
                    size="small"
                    checked={field.required}
                    onChange={v => updateField(index, { required: v })}
                  />
                </div>
              </div>
            </div>

            {/* Type-specific options */}
            {field.type === 'text' && (
              <div className="grid grid-cols-2 gap-2 pt-2 border-t">
                <div>
                  <label className="text-xs text-gray-500">{t('assetTypes.maxLength')}</label>
                  <InputNumber
                    value={field.options?.maxLength}
                    onChange={v => updateFieldOptions(index, { maxLength: v || undefined })}
                    min={1}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">{t('assetTypes.pattern')}</label>
                  <Input
                    value={field.options?.pattern || ''}
                    onChange={e => updateFieldOptions(index, { pattern: e.target.value || undefined })}
                    placeholder="e.g. ^[a-z]+$"
                  />
                </div>
              </div>
            )}

            {field.type === 'number' && (
              <div className="grid grid-cols-3 gap-2 pt-2 border-t">
                <div>
                  <label className="text-xs text-gray-500">{t('assetTypes.min')}</label>
                  <InputNumber
                    value={field.options?.min}
                    onChange={v => updateFieldOptions(index, { min: v ?? undefined })}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">{t('assetTypes.max')}</label>
                  <InputNumber
                    value={field.options?.max}
                    onChange={v => updateFieldOptions(index, { max: v ?? undefined })}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">{t('assetTypes.precision')}</label>
                  <InputNumber
                    value={field.options?.precision}
                    onChange={v => updateFieldOptions(index, { precision: v ?? undefined })}
                    min={0}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">{t('assetTypes.prefix')}</label>
                  <Input
                    value={field.options?.prefix || ''}
                    onChange={e => updateFieldOptions(index, { prefix: e.target.value || undefined })}
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">{t('assetTypes.suffix')}</label>
                  <Input
                    value={field.options?.suffix || ''}
                    onChange={e => updateFieldOptions(index, { suffix: e.target.value || undefined })}
                  />
                </div>
              </div>
            )}

            {field.type === 'select' && (
              <div className="pt-2 border-t">
                <label className="text-xs text-gray-500 block mb-1">{t('assetTypes.choices')}</label>
                <ChoicesEditor
                  choices={field.options?.choices || []}
                  onChange={choices => updateFieldOptions(index, { choices })}
                />
              </div>
            )}

            {field.type === 'textarea' && (
              <div className="grid grid-cols-2 gap-2 pt-2 border-t">
                <div>
                  <label className="text-xs text-gray-500">{t('assetTypes.rows')}</label>
                  <InputNumber
                    value={field.options?.rows}
                    onChange={v => updateFieldOptions(index, { rows: v || undefined })}
                    min={1}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">{t('assetTypes.maxLength')}</label>
                  <InputNumber
                    value={field.options?.maxLength}
                    onChange={v => updateFieldOptions(index, { maxLength: v || undefined })}
                    min={1}
                    className="w-full"
                  />
                </div>
              </div>
            )}

            {field.type === 'relation' && (
              <div className="grid grid-cols-2 gap-2 pt-2 border-t">
                <div>
                  <label className="text-xs text-gray-500">{t('assetTypes.targetType')}</label>
                  <Select
                    value={field.options?.target_type_id}
                    onChange={v => updateFieldOptions(index, { target_type_id: v })}
                    className="w-full"
                    placeholder={t('assetTypes.selectTargetType')}
                  >
                    {(allTypes || [])
                      .filter(at => at.id !== assetType?.id)
                      .map(at => (
                        <Select.Option key={at.id} value={at.id}>
                          {at.name}
                        </Select.Option>
                      ))}
                  </Select>
                </div>
                <div>
                  <label className="text-xs text-gray-500">{t('assetTypes.displayField')}</label>
                  <Input
                    value={field.options?.display_field || ''}
                    onChange={e => updateFieldOptions(index, { display_field: e.target.value || undefined })}
                    placeholder={t('assetTypes.displayFieldPlaceholder')}
                  />
                </div>
              </div>
            )}

            {field.type === 'computed' && (
              <div className="pt-2 border-t">
                <label className="text-xs text-gray-500 block mb-1">{t('assetTypes.expression')}</label>
                <Input.TextArea
                  value={field.options?.expression || ''}
                  onChange={e => updateFieldOptions(index, { expression: e.target.value || undefined })}
                  placeholder={t('assetTypes.expressionPlaceholder')}
                  rows={2}
                />
              </div>
            )}

            {/* Move/Delete buttons */}
            <div className="absolute top-2 right-2 flex gap-1">
              <Button
                size="small"
                icon={<UpOutlined />}
                disabled={index === 0}
                onClick={() => moveField(index, 'up')}
              />
              <Button
                size="small"
                icon={<DownOutlined />}
                disabled={index === fields.length - 1}
                onClick={() => moveField(index, 'down')}
              />
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => removeField(index)}
              />
            </div>
          </Card>
        ))}
      </div>

      <Button
        type="dashed"
        block
        icon={<PlusOutlined />}
        onClick={addField}
        className="mt-3"
      >
        {t('assetTypes.addField')}
      </Button>
    </Modal>
  )
}

// Choices editor for select type
interface ChoicesEditorProps {
  choices: { value: string; label: string }[]
  onChange: (choices: { value: string; label: string }[]) => void
}

function ChoicesEditor({ choices, onChange }: ChoicesEditorProps) {
  const { t } = useTranslation()

  const addChoice = () => {
    onChange([...choices, { value: '', label: '' }])
  }

  const removeChoice = (index: number) => {
    onChange(choices.filter((_, i) => i !== index))
  }

  const updateChoice = (index: number, updates: Partial<{ value: string; label: string }>) => {
    const newChoices = [...choices]
    newChoices[index] = { ...newChoices[index], ...updates }
    onChange(newChoices)
  }

  return (
    <Space direction="vertical" className="w-full">
      {choices.map((choice, index) => (
        <div key={index} className="flex gap-2 items-center">
          <Input
            value={choice.value}
            onChange={e => updateChoice(index, { value: e.target.value })}
            placeholder={t('assetTypes.choiceValue')}
            className="flex-1"
          />
          <Input
            value={choice.label}
            onChange={e => updateChoice(index, { label: e.target.value })}
            placeholder={t('assetTypes.choiceLabel')}
            className="flex-1"
          />
          <Button
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => removeChoice(index)}
          />
        </div>
      ))}
      <Button size="small" type="dashed" icon={<PlusOutlined />} onClick={addChoice}>
        {t('assetTypes.addChoice')}
      </Button>
    </Space>
  )
}
