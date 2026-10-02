import { keepPreviousData, useQueries } from '@tanstack/react-query'

import { useNavContext, usePermission } from '@/core/authorization/use-permission'
import { queryKeys } from '@/shared/constants/query-keys'

import { reportAnalyticsApi } from '../api/report-analytics-api'
import { REPORT_CATALOG, type ReportCatalogEntry } from '../config/report-catalog'
import type { ReportAnalyticsResponse } from '../types/report-analytics'
import { filterVisibleReports } from '../utils/filter-visible-reports'

export interface ReportOverviewEntry {
  report: ReportCatalogEntry
  data?: ReportAnalyticsResponse
  isLoading: boolean
  isError: boolean
}

/**
 * Số liệu dải "Chỉ số chính" của trang Tổng quan — gọi `group_by=none` cho MỌI
 * báo cáo có khai `overviewKpis`, CHỈ khi người dùng đọc được
 * (`can(entity,'read')`), chạy song song bằng `useQueries` (số lượng đổi ĐỘNG
 * theo danh mục, khác `useQuery` không gọi được trong vòng lặp).
 *
 * Không nạp cả trang biểu đồ (`report.load()`) chỉ để lấy vài con số đầu
 * trang — mỗi báo cáo tự khai `endpoint` ngay trong danh mục.
 *
 * `group_by` LUÔN ép về `'none'` ở tầng này bất kể URL đang mang gì (trang
 * Tổng quan không có ô "Xem theo") — phòng trường hợp URL bị gõ tay.
 */
export function useReportOverview(queryParams: Record<string, string>): ReportOverviewEntry[] {
  const { can } = usePermission()
  const { reportKeys } = useNavContext()
  const reports = filterVisibleReports(REPORT_CATALOG, can, reportKeys).filter(
    (r) => r.overviewKpis.length > 0,
  )

  const results = useQueries({
    queries: reports.map((report) => {
      //  `hideCompany`: nguồn không lọc theo công ty ở backend (vd Báo cáo khảo
      //  sát) — đừng gửi `company_id`, kẻo dải KPI của nó trông như đã lọc
      //  trong khi số thật là TOÀN CÔNG TY (L7).
      const params: Record<string, string> = { ...queryParams, group_by: 'none' }
      if (report.hideCompany) delete params.company_id

      return {
        queryKey: queryKeys.report.analytics(report.endpoint, params),
        queryFn: () => reportAnalyticsApi.get(report.endpoint, params),
        placeholderData: keepPreviousData,
      }
    }),
  })

  return reports.map((report, index) => ({
    report,
    data: results[index]?.data,
    isLoading: results[index]?.isLoading ?? false,
    isError: results[index]?.isError ?? false,
  }))
}
