import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/documents/summary',
  exportEndpoint: '/api/documents/summary/export',
  entity: 'document',
  title: 'Báo cáo văn bản',
  description:
    'Tạo mới, ban hành, chờ duyệt, hết hạn trong kỳ — theo loại văn bản, công ty ban hành, phòng chủ trì.',
  slug: 'document',
  sourcePath: appRoutes.document.documents,
  kpis: ['created', 'issued', 'pending', 'expiring', 'avg_turnaround_hours'],
  chartMetric: 'created',
  defaultGroupBy: 'doc_type',
  breakdowns: [
    { key: 'department', title: 'Top phòng chủ trì' },
    { key: 'drafter', title: 'Top người soạn' },
    { key: 'company', title: 'Top công ty ban hành' },
  ],
}

/**
 * Báo cáo Văn bản (phase 05, mục 5.3) — bản BIỂU ĐỒ của phân hệ Báo cáo.
 *
 * Gác CHẶT hơn menu nguồn (`document.read`/`document.export`, Q5.3): mục menu
 * «Văn bản» (`appRoutes.document.documents`) không khai `entity` riêng (cố ý,
 * màn đó có tab «Văn bản đến» mở cho mọi người đăng nhập) nên `report-catalog.
 * test.ts` so khớp với khóa PHÂN HỆ `document` — đúng khóa trang này đang gác.
 *
 * "Chờ duyệt"/"Cần rà soát"/"Hết hạn trong kỳ"/"Đã ban hành" là chỉ số THỜI
 * ĐIỂM (`snapshot`, xem `meta.metrics[].snapshot`) — chỉ có ở thẻ KPI/dòng
 * Tổng, không có trên biểu đồ xu hướng hay từng dòng nhóm.
 */
export function DocumentReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
