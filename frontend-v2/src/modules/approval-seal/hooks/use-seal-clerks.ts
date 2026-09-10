import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import {
  sealClerkApi,
  type SealClerkSyncPayload,
  type SealClerkUpdatePayload,
} from '../api/seal-clerk-api'
import type { SealClerkBulkPayload } from '../types/seal-clerk'

export function useSealClerks(params: ListParams) {
  return useQuery({
    queryKey: queryKeys.sealClerk.list(params),
    queryFn: () => sealClerkApi.list(params),
  })
}

export function useSealClerk(id: number) {
  return useQuery({
    queryKey: [...queryKeys.sealClerk.all, id],
    queryFn: () => sealClerkApi.get(id),
    enabled: id > 0,
  })
}

export function useSealClerkByEmployee(employeeId: number) {
  return useQuery({
    queryKey: [...queryKeys.sealClerk.all, 'by-employee', employeeId],
    queryFn: () => sealClerkApi.byEmployee(employeeId),
    enabled: employeeId > 0,
  })
}

/**
 * Đồng bộ phân công văn thư. `silent` = KHÔNG tự nhả toast xanh — để nơi gọi tự
 * lo thông báo (ví dụ: Xóa cần toast ĐỎ có nút Hoàn tác thay vì "Đã cập nhật").
 */
export function useSyncSealClerks(options?: { silent?: boolean }) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: SealClerkSyncPayload) => sealClerkApi.sync(payload),
    onSuccess: () => {
      if (!options?.silent) toast.success('Đã cập nhật phân công')
      void qc.invalidateQueries({ queryKey: queryKeys.sealClerk.all })
    },
  })
}

export function useUpdateSealClerk(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: SealClerkUpdatePayload) => sealClerkApi.update(id, payload),
    onSuccess: () => {
      toast.success('Đã cập nhật phân công')
      void qc.invalidateQueries({ queryKey: queryKeys.sealClerk.all })
    },
  })
}

export function useSaveSealClerks() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: SealClerkBulkPayload) => sealClerkApi.bulk(payload),
    onSuccess: (res) => {
      toast.success(`Đã phân công ${res.count} mục`)
      void qc.invalidateQueries({ queryKey: queryKeys.sealClerk.all })
    },
  })
}

export function useDeleteSealClerk() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => sealClerkApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa phân công')
      void qc.invalidateQueries({ queryKey: queryKeys.sealClerk.all })
    },
  })
}
