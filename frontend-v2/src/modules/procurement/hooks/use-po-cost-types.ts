/**
 * bao-CR-453 — danh mục Loại chi phí thu mua (`/api/po-cost-types`).
 *
 * Chỉ nạp các loại còn bật, dùng cho ô chọn loại chi phí trên thẻ Chi phí thu
 * mua. Người dùng thiếu quyền `purchase_cost_type.read` thì tắt hẳn truy vấn:
 * ô chọn tự rơi về bộ mã cứng cũ, không ai ăn toast 403 lúc mở đơn.
 */
import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
import { queryKeys } from '@/shared/constants/query-keys'

import type { PoCostType } from '../types/purchase-order-detail'

interface PoCostTypeList {
  items: PoCostType[]
  total: number
}

const LIST_PARAMS = { is_active: true, page_size: 200 }

export function usePoCostTypes() {
  const { can } = usePermission()
  const allowed = can('purchase_cost_type', 'read')

  return useQuery({
    queryKey: queryKeys.procurement.poCostTypes(LIST_PARAMS),
    queryFn: () =>
      apiGet<PoCostTypeList>('/api/po-cost-types', {
        params: { is_active: true, page_size: 200 },
      }),
    enabled: allowed,
    // Danh mục gần như không đổi trong một phiên làm việc.
    staleTime: 5 * 60 * 1000,
  })
}
