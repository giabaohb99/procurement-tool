import { FileText, Workflow } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportCatalogEntry } from './report-catalog'

/**
 * Nhóm HÀNH CHÍNH, phần Văn bản · Phê duyệt (phase 05) — tách khỏi
 * `report-catalog-admin.ts` (Đặt xe · Đóng dấu) chỉ để hai tệp có hai chủ, cùng
 * `group: 'Hành chính'`.
 */
export const DOCUMENT_REPORT_CATALOG: ReportCatalogEntry[] = [
  {
    label: 'Báo cáo văn bản',
    description: 'Tạo mới, ban hành, chờ duyệt, hết hạn trong kỳ — theo loại, công ty, phòng chủ trì.',
    path: appRoutes.report.document,
    //  Mục menu «Văn bản» không khai `entity` riêng (cố ý — xem `modules/document/routes.tsx`),
    //  nên khóa quyền THỰC SỰ gác nó là khóa PHÂN HỆ `document` (luật dự phòng của
    //  `report-catalog.test.ts`). Báo cáo này CHẶT hơn: gác thẳng `document.read`/`.export`.
    sourcePath: appRoutes.document.documents,
    icon: FileText,
    //  ReportKey.DOCUMENT (backend) = 11.
    key: 11,
    entity: 'document',
    group: 'Hành chính',
    endpoint: '/api/documents/summary',
    overviewKpis: ['issued'],
    load: async () => (await import('../pages/document-report-page')).DocumentReportPage,
  },
  {
    label: 'Báo cáo phê duyệt',
    description: 'Phiên duyệt, tỷ lệ duyệt/từ chối/trả về, thời gian xử lý — theo loại chứng từ, người duyệt.',
    path: appRoutes.report.approval,
    //  Khóa quyền của màn Luồng duyệt (`/approval/flows`, mục menu khai thẳng `entity:
    //  'approval_flow'`) — ĐÚNG khóa báo cáo này gác (Q5.4), dù trang biểu đồ không hiện nút
    //  "Xem bảng chi tiết" tới đó (xem ghi chú trong `pages/approval-report-page.tsx`).
    sourcePath: appRoutes.approval.flows,
    icon: Workflow,
    //  ReportKey.APPROVAL (backend) = 12.
    key: 12,
    entity: 'approval_flow',
    group: 'Hành chính',
    hideCompany: true,
    endpoint: '/api/approvals/summary',
    overviewKpis: ['pending'],
    load: async () => (await import('../pages/approval-report-page')).ApprovalReportPage,
  },
]
