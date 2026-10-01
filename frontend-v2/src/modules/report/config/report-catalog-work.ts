import { ListChecks } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportCatalogEntry } from './report-catalog'

/**
 * Nhóm DỰ ÁN của danh mục báo cáo (phase 06) — một báo cáo "Công việc & Dự án"
 * (`pages/work-report-page.tsx`): việc tạo mới/hoàn thành theo kỳ, đang mở, quá
 * hạn, tỷ lệ đúng hạn — theo dự án · nhóm dự án · người phụ trách · công ty ·
 * trạng thái · độ ưu tiên. Bảng dự án gốc vẫn ở `/project/lists` (`sourcePath`).
 */
export const WORK_REPORT_CATALOG: ReportCatalogEntry[] = [
  {
    label: 'Công việc & Dự án',
    description:
      'Việc tạo mới/hoàn thành theo kỳ, đang mở, quá hạn, tỷ lệ đúng hạn — theo dự án và người phụ trách.',
    path: appRoutes.report.work,
    sourcePath: appRoutes.project.list,
    icon: ListChecks,
    entity: 'work_task',
    group: 'Dự án',
    endpoint: '/api/work/summary',
    //  Khớp `hideCompany: true` của `work-report-page.tsx` — `work_task` PUBLIC
    //  ở `SCOPE_FIELDS`, phạm vi thật là TƯ CÁCH THÀNH VIÊN dự án chứ không phải
    //  pháp nhân (H1, review 01/10/2026 — thiếu dòng này thì trang Tổng quan vẫn
    //  gửi `company_id` cho báo cáo này dù trang biểu đồ đã bỏ ô lọc Công ty).
    hideCompany: true,
    //  "Quá hạn" là con số đáng hỏi nhất của phân hệ — khớp cách các báo cáo
    //  khác chọn 1 chỉ số "cần hành động" cho dải KPI Tổng quan (vd `late`,
    //  `late_deliveries`, `idle_lines`).
    overviewKpis: ['overdue_tasks'],
    load: async () => (await import('../pages/work-report-page')).WorkReportPage,
  },
]
