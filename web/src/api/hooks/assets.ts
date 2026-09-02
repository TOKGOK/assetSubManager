import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../client'
import type { Asset, CreateAssetRequest, UpdateAssetRequest, AssetListParams } from '../../types/asset'
import type { ListData } from '../../types'

// ===== 统一资产 Hooks =====

export function useAssets(params?: AssetListParams) {
  return useQuery({
    queryKey: ['assets', params],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: ListData<Asset> }>('/assets/', { params })
      return data.data
    },
    staleTime: 30_000,
  })
}

export function useAsset(id: number) {
  return useQuery({
    queryKey: ['asset', id],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: Asset }>(`/assets/${id}`)
      return data.data
    },
    enabled: id > 0,
  })
}

export function useCreateAsset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: CreateAssetRequest) =>
      client.post('/assets/', req).then(r => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['category-stats'] })
    },
  })
}

export function useUpdateAsset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...req }: UpdateAssetRequest & { id: number }) =>
      client.put(`/assets/${id}`, req).then(r => r.data.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['assets'] })
      qc.invalidateQueries({ queryKey: ['asset', vars.id] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['category-stats'] })
    },
  })
}

export function useDeleteAsset() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => client.delete(`/assets/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['category-stats'] })
    },
  })
}

export function useBatchDeleteAssets() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ids: number[]) =>
      client.post('/assets/batch-delete', { ids }).then(r => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assets'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['category-stats'] })
    },
  })
}
