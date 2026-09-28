import { apiGet, downloadFile } from '@/core/api'

import type { ReportAnalyticsResponse } from '../types/report-analytics'

/**
 * Hai thao tác của MỌI trang báo cáo Haravan: đọc số liệu và xuất Excel — cùng
 * bộ tham số (`preset|date_from,date_to · compare · group_by · company_id` +
 * lọc riêng của trang), chỉ khác đường và cách nhận kết quả.
 */
export const reportAnalyticsApi = {
  get: (endpoint: string, params: Record<string, string>) =>
    apiGet<ReportAnalyticsResponse>(endpoint, { params }),
  export: (endpoint: string, params: Record<string, string>, filename: string) =>
    downloadFile(endpoint, filename, params),
}
