import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../client'
import type { Category, CreateCategoryRequest, UpdateCategoryRequest } from '../../types'

// ===== 按资产类型获取分类树 =====

export function useCategoriesByType(typeId: number) {
  return useQuery({
    queryKey: ['categories-by-type', typeId],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: Category[] }>(`/asset-types/${typeId}/categories/`)
      return data.data
    },
    enabled: typeId > 0,
    staleTime: 5 * 60_000,
  })
}

// ===== 按资产类型创建分类 =====

export function useCreateCategoryByType(typeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (req: CreateCategoryRequest) =>
      client.post(`/asset-types/${typeId}/categories/`, req).then(r => r.data.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['categories-by-type', typeId] })
    },
  })
}

// ===== 获取单个分类 =====

export function useCategory(id: number) {
  return useQuery({
    queryKey: ['category', id],
    queryFn: async () => {
      const { data } = await client.get<{ code: number; data: Category }>(`/categories/${id}`)
      return data.data
    },
    enabled: id > 0,
  })
}

// ===== 更新分类 =====

export function useUpdateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...req }: UpdateCategoryRequest & { id: number }) =>
      client.put(`/categories/${id}`, req).then(r => r.data.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['category', vars.id] })
      // Invalidate all category-by-type queries since we don't know which type it belongs to
      qc.invalidateQueries({ queryKey: ['categories-by-type'] })
    },
  })
}

// ===== 删除分类 =====

export function useDeleteCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => client.delete(`/categories/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['categories-by-type'] })
      qc.invalidateQueries({ queryKey: ['category'] })
    },
  })
}
