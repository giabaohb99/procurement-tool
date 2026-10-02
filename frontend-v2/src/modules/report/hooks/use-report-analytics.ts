import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { reportAnalyticsApi } from '../api/report-analytics-api'

/**
 * Dữ liệu MỘT trang báo cáo Haravan.
 *
 * `keepPreviousData`: đổi kỳ / so sánh / "Xem theo" mà cả trang nháy về khung
 * rỗng là mất ngữ cảnh đang so — giữ số cũ tới khi số mới về (cùng lý do bốn
 * hook `use-report-summaries.ts` cũ đã áp dụng).
 */
export function useReportAnalytics(endpoint: string, params: Record<string, string>) {
  return useQuery({
    queryKey: queryKeys.report.analytics(endpoint, params),
    queryFn: () => reportAnalyticsApi.get(endpoint, params),
    placeholderData: keepPreviousData,
  })
}
