import type { AssetType } from './asset-type'
import type { Category } from './index'

// ===== 统一资产类型 =====

export interface Asset {
  id: number
  type_id: number
  category_id?: number
  name: string
  custom_data: Record<string, any>
  computed_fields?: Record<string, any>
  created_at: string
  updated_at: string
  // joined
  asset_type?: AssetType
  category?: Category
}

// ===== 请求/响应类型 =====

export interface CreateAssetRequest {
  type_id: number
  category_id?: number
  name: string
  custom_data?: Record<string, any>
}

export interface UpdateAssetRequest {
  category_id?: number
  name?: string
  custom_data?: Record<string, any>
}

export interface AssetListParams {
  type_id?: number
  type_ids?: string
  category_id?: number
  search?: string
  status?: string
  page?: number
  page_size?: number
}
