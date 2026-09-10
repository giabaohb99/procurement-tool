import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { sealDashboardApi, type SealOverviewParams } from '../api/seal-dashboard-api'

/**
 * Số liệu trang Tổng quan Duyệt dấu — một lần gọi cho cả trang, backend gom sẵn
 * các khối theo vai trò của người đang đăng nhập. `params` chỉ đổi khối "Theo trạng
 * thái" (lọc theo khoảng ngày) nên nằm trong query-key để tự nạp lại khi đổi.
 */
export function useSealDashboard(params?: SealOverviewParams) {
  return useQuery({
    queryKey: queryKeys.sealRequest.overview({
      date_from: params?.date_from ?? '',
      date_to: params?.date_to ?? '',
    }),
    queryFn: () => sealDashboardApi.getOverview(params),
  })
}
