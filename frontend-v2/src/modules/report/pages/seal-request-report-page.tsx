import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/seal-requests/summary',
  exportEndpoint: '/api/seal-requests/summary/export',
  entity: 'seal_request',
  title: 'Báo cáo đóng dấu',
  description:
    'Đề nghị, đã đóng dấu, tỷ lệ từ chối, thời gian duyệt và thời gian duyệt → đóng dấu — theo loại dấu, công ty, văn thư.',
  slug: 'duyet-dong-dau',
  sourcePath: appRoutes.approvalSeal.requests,
  kpis: ['requests', 'completed', 'reject_rate', 'avg_approve_complete_hours'],
  chartMetric: 'requests',
  defaultGroupBy: 'status',
  breakdowns: [
    { key: 'status', title: 'Theo trạng thái' },
    { key: 'seal_type', title: 'Theo loại dấu' },
  ],
}

/**
 * Báo cáo Duyệt đóng dấu (phase 05, 5.2) — bản BIỂU ĐỒ kiểu Haravan của phân hệ
 * Duyệt dấu.
 *
 * Kỳ tính theo NGÀY TẠO (`created_at`, Q5.2). Cùng `require`/`apply_scope` với
 * danh sách Yêu cầu đóng dấu (`sourcePath`) — GIỮ NGUYÊN luật công ty/văn thư:
 * người xem phạm vi công ty chỉ thấy phiếu ĐÃ DUYỆT/HOÀN THÀNH, nên số của họ
 * khác số của phòng tạo phiếu (đúng luật hiện có, backend ghi `notes` khi cần).
 * Một phiếu gắn NHIỀU công ty thì chiều "Công ty" góp mặt ở NHIỀU nhóm, Tổng vẫn
 * tính độc lập — không phải lỗi cộng dồn.
 */
export function SealRequestReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
