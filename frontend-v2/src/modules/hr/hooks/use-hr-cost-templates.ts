import { useQuery } from '@tanstack/react-query'

import { getCrudDetailKey, getCrudQueryKey } from '@/shared/crud'
import { HR_COST_GROUP_API_PATH, HR_COST_TEMPLATE_API_PATH, hrCostApi } from '../api/hr-cost-template-api'

/**
 * Hook ĐỌC nhóm chi phí + mẫu khoản chi phí (duoc-CR-690). Giữ khóa của khung CRUD chung
 * (`['crud', apiPath, …]`) để nếu sau này có màn ghi thì quét đúng gốc đó là đủ.
 */

export function useHrCostGroups(enabled = true) {
  return useQuery({
    queryKey: getCrudQueryKey(HR_COST_GROUP_API_PATH, { lookup: true }),
    queryFn: hrCostApi.listGroups,
    enabled,
    staleTime: 60_000,
  })
}

/** Các mẫu đang dùng — trang kế hoạch mới lấy «Mẫu gợi ý» (hoặc mẫu đầu tiên) để điền sẵn chi phí. */
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
