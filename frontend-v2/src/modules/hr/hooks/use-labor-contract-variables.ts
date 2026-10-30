import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { laborContractVariableApi } from '../api/labor-contract-variable-api'
import type {
  LaborContractVariableCreatePayload,
  LaborContractVariableUpdatePayload,
} from '../types/labor-contract-variable'

export function useLaborContractVariables(params: ListParams, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.hr.laborContractVariables(params),
    queryFn: () => laborContractVariableApi.list(params),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}

/** Chi tiết MỘT biến (nơi đang dùng + cờ khóa mã) — chỉ nạp khi hộp sửa mở. */
export function useLaborContractVariable(id: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.laborContractVariable(id),
    queryFn: () => laborContractVariableApi.get(id),
    enabled: enabled && id > 0,
  })
}

/** Ô nhập biến trong hộp Lập / Sửa hợp đồng. Chỉ nạp khi hộp mở. */
export function useLaborContractInputFields(enabled: boolean, includeInactive: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.laborContractVariableInputFields(includeInactive),
    queryFn: () => laborContractVariableApi.inputFields(includeInactive),
    enabled,
  })
}

/** Mọi lệnh ghi quét `hr.all`: bảng, khung "Chèn biến" (đọc `/placeholders`), ô nhập trong hộp HĐ cùng mới. */
function useInvalidateHr() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
}

export function useCreateLaborContractVariable() {
  const invalidate = useInvalidateHr()
  return useMutation({
    mutationFn: (payload: LaborContractVariableCreatePayload) => laborContractVariableApi.create(payload),
    onSuccess: () => {
      toast.success('Đã thêm biến')
      void invalidate()
    },
  })
}

export function useUpdateLaborContractVariable() {
  const invalidate = useInvalidateHr()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: LaborContractVariableUpdatePayload }) =>
      laborContractVariableApi.update(id, payload),
    onSuccess: (_data, { payload }) => {
      if (payload.is_active !== undefined) toast.success(payload.is_active ? 'Đã bật dùng biến' : 'Đã ngừng dùng biến')
      else if (payload.is_hidden !== undefined) toast.success(payload.is_hidden ? 'Đã ẩn biến' : 'Đã hiện biến')
      else toast.success('Đã cập nhật biến')
      void invalidate()
    },
  })
}

export function useDeleteLaborContractVariable() {
  const invalidate = useInvalidateHr()
  return useMutation({
    mutationFn: (id: number) => laborContractVariableApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa biến')
      void invalidate()
    },
  })
}
