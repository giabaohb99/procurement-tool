import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { productionDashboardApi } from '../api/production-dashboard-api'

/**
 * Số liệu trang Tổng quan Sản xuất. Một lần gọi cho cả trang.
 *
 * Không cần `enabled`: endpoint chỉ đòi đăng nhập rồi tự gác từng khối theo
 * quyền, nên không có nhánh nào ăn 403. Trước đây trang này ghép năm lời gọi
 * danh sách với `page_size=1` để lấy `total` — mỗi lời gọi là một endpoint có
 * `require(...)`, thiếu quyền cái nào là ăn một toast 403 ngay lúc mở trang.
 */
export function useProductionDashboard() {
  return useQuery({
    queryKey: queryKeys.production.dashboard(),
    queryFn: () => productionDashboardApi.getOverview(),
  })
}
