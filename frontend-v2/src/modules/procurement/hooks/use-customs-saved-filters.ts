import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'

import {
  createCustomsSavedFilter,
  deleteCustomsSavedFilter,
  fetchCustomsBatchRows,
  fetchCustomsBatchRowSummary,
  fetchCustomsSavedFilters,
  updateCustomsSavedFilter,
} from '../api/customs-saved-filter-api'

/** bao-CR-496 — bộ lọc đã lưu của người đang đăng nhập. */
export function useCustomsSavedFilters(enabled = true) {
  return useQuery({
    queryKey: queryKeys.procurement.customsSavedFilters(),
    queryFn: fetchCustomsSavedFilters,
    enabled,
    staleTime: 60_000,
  })
}

export function useCustomsSavedFilterMutations() {
  const qc = useQueryClient()
  const refresh = () =>
    qc.invalidateQueries({ queryKey: queryKeys.procurement.customsSavedFilters() })

  const create = useMutation({
    mutationFn: createCustomsSavedFilter,
    onSuccess: (f) => {
      toast.success(`Đã lưu bộ lọc «${f.name}»`)
      void refresh()
    },
  })
  const update = useMutation({
    mutationFn: ({ id, ...body }: { id: number; name?: string; params?: string }) =>
      updateCustomsSavedFilter(id, body),
    onSuccess: (f) => {
      toast.success(`Đã cập nhật bộ lọc «${f.name}»`)
      void refresh()
    },
  })
  const remove = useMutation({
    mutationFn: deleteCustomsSavedFilter,
    onSuccess: () => {
      toast.success('Đã xóa bộ lọc')
      void refresh()
    },
  })
  return { create, update, remove }
}

/** bao-CR-496 — tổng theo kết cục của một lô. */
export function useCustomsBatchRowSummary(batchId: number | null) {
  return useQuery({
    queryKey: queryKeys.procurement.customsBatchRowSummary(batchId ?? 0),
    queryFn: () => fetchCustomsBatchRowSummary(batchId ?? 0),
    enabled: batchId !== null,
  })
}

/** bao-CR-496 — danh sách từng dòng của một lô, lọc theo kết cục, phân trang. */
export function useCustomsBatchRows(
  batchId: number | null,
  params: { page: number; page_size: number; row_status?: number },
) {
  return useQuery({
    queryKey: queryKeys.procurement.customsBatchRows(batchId ?? 0, params),
    queryFn: () => fetchCustomsBatchRows(batchId ?? 0, params),
    enabled: batchId !== null,
    placeholderData: (prev) => prev,
  })
}
