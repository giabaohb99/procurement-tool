import type { ReportPageConfig } from '../types/report-analytics'
import { ReportAnalyticsPage } from './report-analytics-page'

const CONFIG: ReportPageConfig = {
  endpoint: '/api/approvals/summary',
  exportEndpoint: '/api/approvals/summary/export',
  entity: 'approval_flow',
  title: 'Báo cáo phê duyệt',
  description:
    'Phiên duyệt, tỷ lệ duyệt/từ chối/trả về, thời gian xử lý — theo loại chứng từ, người duyệt, bước.',
  slug: 'approval',
  //  CỐ Ý không khai `sourcePath` — ẩn nút "Xem bảng chi tiết": `/approval/flows` là màn
  //  CẤU HÌNH LUỒNG (danh mục bước/người duyệt), không phải bảng DÒNG PHIÊN mà báo cáo này
  //  đang tổng hợp. Danh mục (`report-catalog-document.ts`) vẫn khai `sourcePath` tới đó vì
  //  khóa quyền gác trang này (`approval_flow`) đúng là khóa của màn Luồng duyệt.
  kpis: ['sessions', 'approved', 'rejected', 'avg_proc_hours', 'step_overdue_rate'],
  chartMetric: 'sessions',
  defaultGroupBy: 'entity',
  breakdowns: [
    { key: 'approver', title: 'Top người duyệt' },
    { key: 'node_name', title: 'Top bước' },
  ],
  //  Phiên duyệt không gắn công ty riêng (mượn phạm vi từ chứng từ gốc, xem
  //  `approval/report_service.py`) — ẩn ô lọc Công ty, khớp `hideCompany` của danh mục.
  hideCompany: true,
}

/**
 * Báo cáo Phê duyệt (phase 05, mục 5.4) — bản BIỂU ĐỒ của phân hệ Báo cáo.
 *
 * Gác bằng `approval_flow.read`/`.export` (thường chỉ quản trị/HCNS, Q5.4). Số
 * liệu vẫn lọc riêng theo quyền đọc TỪNG loại chứng từ nguồn ở backend — thiếu
 * `document.read` thì phiên "Văn bản" biến mất khỏi mọi số, kể cả khi người xem
 * có đủ quyền xem báo cáo này (xem `notes` backend trả về khi có loại bị loại).
 */
export function ApprovalReportPage() {
  return <ReportAnalyticsPage config={CONFIG} />
}
