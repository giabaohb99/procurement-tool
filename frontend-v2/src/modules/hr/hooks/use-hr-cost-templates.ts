import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { getCrudDetailKey, getCrudQueryKey, getCrudRootKey } from '@/shared/crud'
import {
  HR_COST_GROUP_API_PATH,
  HR_COST_TEMPLATE_API_PATH,
  hrCostApi,
} from '../api/hr-cost-template-api'
import type { HrCostTemplatePayload } from '../types/hr-cost'

/**
 * Hook của NHÓM CHI PHÍ + MẪU KHOẢN CHI PHÍ (duoc-CR-690). Cố ý dùng khóa của khung CRUD chung
 * (`['crud', apiPath, …]`): màn danh mục chạy trên `CrudListPage` quét đúng gốc đó sau mỗi lần ghi,
 * nên ô chọn «Nhóm» / «Mẫu» ở trang khác tự nạp lại mà không ai phải nhớ gọi thêm.
 */

export function useHrCostGroups(enabled = true) {
  return useQuery({
    queryKey: getCrudQueryKey(HR_COST_GROUP_API_PATH, { lookup: true }),
    queryFn: hrCostApi.listGroups,
    enabled,
    staleTime: 60_000,
  })
}

/** Ô chọn «Mẫu khoản chi phí» lúc tạo kế hoạch — chỉ mẫu đang dùng. */
export function useActiveHrCostTemplates(enabled = true) {
  const params = { is_active: true, lookup: true }
  return useQuery({
    queryKey: getCrudQueryKey(HR_COST_TEMPLATE_API_PATH, params),
    queryFn: () => hrCostApi.listTemplates({ is_active: true }),
    enabled,
  })
}

export function useHrCostTemplate(id: number) {
  return useQuery({
    queryKey: getCrudDetailKey(HR_COST_TEMPLATE_API_PATH, id),
    queryFn: () => hrCostApi.getTemplate(id),
    enabled: id > 0,
  })
}

function useInvalidateTemplates() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: getCrudRootKey(HR_COST_TEMPLATE_API_PATH) })
}

export function useSaveHrCostTemplate() {
  const invalidate = useInvalidateTemplates()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: HrCostTemplatePayload }) =>
      id > 0 ? hrCostApi.updateTemplate(id, payload) : hrCostApi.createTemplate(payload),
    onSuccess: (_data, { id }) => {
      toast.success(id > 0 ? 'Đã lưu mẫu khoản chi phí' : 'Đã tạo mẫu khoản chi phí')
      void invalidate()
    },
  })
}

export function useDuplicateHrCostTemplate() {
  const invalidate = useInvalidateTemplates()
  return useMutation({
    mutationFn: hrCostApi.duplicateTemplate,
    onSuccess: () => {
      toast.success('Đã nhân bản mẫu — đang mở bản sao')
      void invalidate()
    },
  })
}

export function useDeleteHrCostTemplate() {
  const invalidate = useInvalidateTemplates()
  return useMutation({
    mutationFn: hrCostApi.removeTemplate,
    onSuccess: () => {
      toast.success('Đã xóa mẫu khoản chi phí')
      void invalidate()
    },
  })
}
