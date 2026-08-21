import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { contractApi } from '../api/contract-api'
import type { Contract } from '../types/contract'

/**
 * Danh sách hợp đồng có phân trang.
 *
 * `enabled`: backend chặn `contract.read`, không có quyền mà vẫn gọi thì người
 * dùng ăn một toast 403 ngay khi mở tab — thà đừng gọi.
 */
export function useContracts(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }

  return useQuery({
    queryKey: queryKeys.production.contracts(query),
    queryFn: () => contractApi.list(query),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}

export function useContract(id: number) {
  return useQuery({
    queryKey: queryKeys.production.contract(id),
    queryFn: () => contractApi.getById(id),
    enabled: id > 0,
  })
}

export function useCreateContract() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Contract>) => contractApi.create(data),
    onSuccess: (newContract) => {
      queryClient.setQueryData(queryKeys.production.contract(newContract.id), newContract)
      void queryClient.invalidateQueries({ queryKey: queryKeys.production.allContracts })
      toast.success(`Đã tạo hợp đồng ${newContract.code}`)
    },
  })
}

export function useUpdateContract(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Contract>) => contractApi.update(id, data),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKeys.production.contract(id), updated)
      void queryClient.invalidateQueries({ queryKey: queryKeys.production.allContracts })
      toast.success(`Đã cập nhật hợp đồng ${updated.code}`)
    },
  })
}

export function useDeleteContract() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => contractApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.production.allContracts })
      toast.success('Đã xóa hợp đồng')
    },
  })
}

export function useBulkDeleteContracts() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (ids: number[]) => contractApi.bulkDelete(ids),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.production.allContracts })
      toast.success('Đã xóa các hợp đồng đã chọn')
    },
  })
}
