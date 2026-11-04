import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { orgChartApi } from '../api/org-chart-api'

/**
 * Dữ liệu PHẲNG của sơ đồ tổ chức. Đọc thẳng mỗi lần mở (không lưu bản vẽ), nên đổi phòng /
 * quản lý là sơ đồ đổi theo; cây do trang dựng bằng `buildOrgChartForest`.
 */
export function useOrgChart(options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.hr.orgChart(),
    queryFn: orgChartApi.get,
    enabled: options.enabled ?? true,
  })
}
