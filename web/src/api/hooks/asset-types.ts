import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../client'
import type {
  AssetType,
  CreateAssetTypeRequest,
  UpdateAssetTypeRequest,
} from '../../types/asset-type'

// ===== 资产类型 Hooks =====

export function useAssetTypes() {
  return useQuery({
    queryKey: ['asset-types'],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: AssetType[] }>('/asset-types/')
      return data.data
    },
    staleTime: 5 * 60_000,
  })
}

export function useAssetType(id: number) {
  return useQuery({
    queryKey: ['asset-type', id],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: AssetType }>(`/asset-types/${id}`)
      return data.data
    },
    enabled: id > 0,
  })
}

export function useCreateAssetType() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: CreateAssetTypeRequest) =>
      client.post('/asset-types/', req).then(r => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['asset-types'] })
    },
  })
}

export function useUpdateAssetType() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...req }: UpdateAssetTypeRequest & { id: number }) =>
      client.put(`/asset-types/${id}`, req).then(r => r.data.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['asset-types'] })
      qc.invalidateQueries({ queryKey: ['asset-type', vars.id] })
    },
  })
}

export function useDeleteAssetType() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => client.delete(`/asset-types/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['asset-types'] })
    },
  })
}
