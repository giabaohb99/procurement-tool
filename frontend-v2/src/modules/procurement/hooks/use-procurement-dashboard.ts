import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { procurementDashboardApi } from '../api/procurement-dashboard-api'

/**
 * Số liệu trang Tổng quan Thu mua. Một lần gọi cho cả trang — backend đã gom
 * sẵn KPI, chi phí 12 tháng, cảnh báo và chứng từ gần đây.
 */
export function useProcurementDashboard() {
  return useQuery({
    queryKey: queryKeys.procurement.dashboard(),
    queryFn: () => procurementDashboardApi.getOverview(),
  })
}
