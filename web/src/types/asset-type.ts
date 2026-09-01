// ===== 资产类型定义 =====

export type FieldType =
  | 'text'
  | 'number'
  | 'boolean'
  | 'date'
  | 'datetime'
  | 'select'
  | 'textarea'
  | 'relation'
  | 'computed'

export interface FieldOptions {
  // text
  maxLength?: number
  pattern?: string
  // number
  min?: number
  max?: number
  precision?: number
  prefix?: string
  suffix?: string
  // select (static choices)
  choices?: Array<{ value: string; label: string }>
  // select (dynamic from API)
  api_endpoint?: string
  value_field?: string
  label_field?: string
  // textarea
  rows?: number
  // relation
  target_type_id?: number
  display_field?: string
  // computed
  expression?: string
}

export interface FieldDefinition {
  key: string
  label: string
  type: FieldType
  required?: boolean
  options?: FieldOptions
}

export interface FieldConfig {
  fields: FieldDefinition[]
}

export interface AssetType {
  id: number
  name: string
  icon?: string
  field_config: FieldConfig
  is_system: boolean
  created_at: string
  updated_at: string
}

// ===== 请求/响应类型 =====

export interface CreateAssetTypeRequest {
  name: string
  icon?: string
  field_config: FieldConfig
  is_system?: boolean
}

export interface UpdateAssetTypeRequest {
  name?: string
  icon?: string
  field_config?: FieldConfig
}
