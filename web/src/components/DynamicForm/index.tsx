import { useMemo, useState, useEffect } from 'react'
import { Form, Input, InputNumber, Switch, DatePicker, Select } from 'antd'
import dayjs from 'dayjs'
import { useTranslation } from 'react-i18next'
import i18n from '../../i18n'
import type { FieldConfig, FieldDefinition } from '../../types/asset-type'
import { useAssets } from '../../api/hooks/assets'
import client from '../../api/client'

interface DynamicFormProps {
  fieldConfig: FieldConfig
  values: Record<string, any>
  onChange: (values: Record<string, any>) => void
  errors?: Record<string, string>
  disabled?: boolean
}

// 简单表达式引擎：支持四则运算和变量引用
function evaluateExpression(expression: string, values: Record<string, any>): any {
  try {
    // 将字段名替换为值
    let expr = expression
    // 按长度降序替换，避免子串问题
    const keys = Object.keys(values).sort((a, b) => b.length - a.length)
    for (const key of keys) {
      const val = values[key]
      const numVal = typeof val === 'number' ? val : parseFloat(val)
      const replacement = isNaN(numVal) ? '0' : String(numVal)
      expr = expr.replace(new RegExp(`\\b${key}\\b`, 'g'), replacement)
    }
    // 安全计算
    const fn = new Function(`"use strict"; return (${expr})`)
    return fn()
  } catch {
    return '--'
  }
}

// 关联字段选项加载组件
function RelationSelect({
  field,
  value,
  onChange,
  disabled,
}: {
  field: FieldDefinition
  value?: any
  onChange?: (val: any) => void
  disabled?: boolean
}) {
  const { t } = useTranslation()
  const opts = field.options ?? {}
  const { data, isLoading, error } = useAssets(
    opts.target_type_id ? { type_id: opts.target_type_id, page_size: 9999 } : undefined,
  )

  const options = useMemo(() => {
    if (!data?.items) return []
    return data.items.map((item) => ({
      value: item.id,
      label: opts.display_field
        ? String(item.custom_data?.[opts.display_field] ?? item.name ?? item.id)
        : item.name,
    }))
  }, [data, opts.display_field])

  return (
    <Select
      showSearch
      allowClear
      loading={isLoading}
      options={options}
      value={value}
      onChange={onChange}
      disabled={disabled}
      placeholder={error ? t('common.loadingFailed') : t('common.selectPlaceholder')}
      filterOption={(input, option) =>
        (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
      }
    />
  )
}

// 动态 API 数据源选择组件
function DynamicSelect({
  field,
  value,
  onChange,
  disabled,
}: {
  field: FieldDefinition
  value?: any
  onChange?: (val: any) => void
  disabled?: boolean
}) {
  const { t } = useTranslation()
  const opts = field.options ?? {}
  const [options, setOptions] = useState<Array<{ value: any; label: string }>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!opts.api_endpoint) return

    setLoading(true)
    setError(null)
    client
      .get(opts.api_endpoint)
      .then((res) => {
        const items = res.data?.data ?? res.data ?? []
        const list = Array.isArray(items) ? items : []
        const valueField = opts.value_field ?? 'id'
        const labelField = opts.label_field ?? 'name'
        setOptions(
          list.map((item: any) => ({
            value: item[valueField],
            label: String(item[labelField] ?? item.id ?? ''),
          })),
        )
      })
      .catch((err) => {
        setError(err?.message ?? t('common.loadingFailed'))
      })
      .finally(() => {
        setLoading(false)
      })
  }, [opts.api_endpoint, opts.value_field, opts.label_field])

  return (
    <Select
      showSearch
      allowClear
      loading={loading}
      options={options}
      value={value}
      onChange={onChange}
      disabled={disabled}
      placeholder={error ?? t('common.selectPlaceholder')}
      filterOption={(input, option) =>
        (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
      }
    />
  )
}

function renderField(
  field: FieldDefinition,
  value: any,
  onChange: (val: any) => void,
  disabled?: boolean,
  allValues?: Record<string, any>,
) {
  const opts = field.options ?? {}

  switch (field.type) {
    case 'text':
      return (
        <Input
          maxLength={opts.maxLength}
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
        />
      )

    case 'number':
      return (
        <InputNumber
          min={opts.min}
          max={opts.max}
          precision={opts.precision}
          prefix={opts.prefix}
          suffix={opts.suffix}
          value={value}
          onChange={onChange}
          disabled={disabled}
          style={{ width: '100%' }}
        />
      )

    case 'boolean':
      return (
        <Switch
          checked={!!value}
          onChange={onChange}
          disabled={disabled}
        />
      )

    case 'date':
      return (
        <DatePicker
          style={{ width: '100%' }}
          value={value ? dayjs(value) : undefined}
          onChange={(_date, dateString) => onChange(dateString)}
          disabled={disabled}
          disabledDate={(current) => {
            if (!current) return false
            if (opts.min && current.isBefore(dayjs(opts.min), 'day')) return true
            if (opts.max && current.isAfter(dayjs(opts.max), 'day')) return true
            return false
          }}
        />
      )

    case 'datetime':
      return (
        <DatePicker
          showTime
          style={{ width: '100%' }}
          value={value ? dayjs(value) : undefined}
          onChange={(_date, dateString) => onChange(dateString)}
          disabled={disabled}
          disabledDate={(current) => {
            if (!current) return false
            if (opts.min && current.isBefore(dayjs(opts.min), 'day')) return true
            if (opts.max && current.isAfter(dayjs(opts.max), 'day')) return true
            return false
          }}
        />
      )

    case 'select':
      if (opts.api_endpoint) {
        return (
          <DynamicSelect
            field={field}
            value={value}
            onChange={onChange}
            disabled={disabled}
          />
        )
      }
      return (
        <Select
          allowClear
          options={opts.choices ?? []}
          value={value}
          onChange={onChange}
          disabled={disabled}
          placeholder={i18n.t('common.selectPlaceholder')}
        />
      )

    case 'textarea':
      return (
        <Input.TextArea
          rows={opts.rows ?? 4}
          maxLength={opts.maxLength}
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
        />
      )

    case 'relation':
      return (
        <RelationSelect
          field={field}
          value={value}
          onChange={onChange}
          disabled={disabled}
        />
      )

    case 'computed': {
      const result =
        allValues && opts.expression
          ? evaluateExpression(opts.expression, allValues)
          : '--'
      return <span style={{ color: '#999' }}>{result ?? '--'}</span>
    }

    default:
      return <div>{i18n.t('common.unknownFieldType')}: {field.type}</div>
  }
}

export function validateForm(
  fieldConfig: FieldConfig,
  values: Record<string, any>,
): Record<string, string> {
  const errors: Record<string, string> = {}

  for (const field of fieldConfig.fields) {
    if (field.type === 'computed') continue

    const val = values[field.key]

    if (field.required && (val === undefined || val === null || val === '')) {
      errors[field.key] = i18n.t('common.fieldRequired')
      continue
    }

    if (val === undefined || val === null || val === '') continue

    if (field.type === 'number') {
      const num = typeof val === 'number' ? val : parseFloat(val)
      if (isNaN(num)) {
        errors[field.key] = i18n.t('common.invalidNumber')
      } else {
        if (field.options?.min !== undefined && num < field.options.min) {
          errors[field.key] = i18n.t('common.minValue', { min: field.options.min })
        }
        if (field.options?.max !== undefined && num > field.options.max) {
          errors[field.key] = i18n.t('common.maxValue', { max: field.options.max })
        }
      }
    }

    if (field.type === 'text' && field.options?.pattern) {
      const regex = new RegExp(field.options.pattern)
      if (!regex.test(String(val))) {
        errors[field.key] = i18n.t('common.invalidFormat')
      }
    }
  }

  return errors
}

export default function DynamicForm({
  fieldConfig,
  values,
  onChange,
  errors,
  disabled,
}: DynamicFormProps) {
  const handleChange = (key: string, val: any) => {
    const newValues = { ...values, [key]: val }

    // 重新计算 computed 字段
    for (const field of fieldConfig.fields) {
      if (field.type === 'computed' && field.options?.expression) {
        newValues[field.key] = evaluateExpression(field.options.expression, newValues)
      }
    }

    onChange(newValues)
  }

  return (
    <Form layout="vertical">
      {fieldConfig.fields.map((field) => {
        const error = errors?.[field.key]
        return (
          <Form.Item
            key={field.key}
            label={field.label}
            required={field.required}
            validateStatus={error ? 'error' : undefined}
            help={error}
          >
            {renderField(field, values[field.key], (val) => handleChange(field.key, val), disabled, values)}
          </Form.Item>
        )
      })}
    </Form>
  )
}
