import { CalendarOff, IdCard, Wallet } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportCatalogEntry } from './report-catalog'

/**
 * Nhóm NHÂN SỰ của danh mục báo cáo (phase 04) — Nhân sự (biến động & cơ cấu) ·
 * Nghỉ phép (tình hình nghỉ) · Quỹ phép năm. Mỗi báo cáo = một `ReportPageConfig`
 * (`pages/hr-headcount-report-page.tsx`/`leave-usage-report-page.tsx`/
 * `leave-balance-report-page.tsx`) — xem các tệp đó để biết KPI/chỉ số xu
 * hướng/breakdown/nhóm mặc định.
 */
export const HR_REPORT_CATALOG: ReportCatalogEntry[] = [
  {
    label: 'Biến động nhân sự',
    description: 'Định biên đầu/cuối kỳ, vào mới, nghỉ việc, tỷ lệ nghỉ việc theo phòng ban/cấp bậc.',
    path: appRoutes.report.hrHeadcount,
    sourcePath: appRoutes.hr.employees,
    icon: IdCard,
    //  ReportKey.HR_HEADCOUNT (backend) = 6.
    key: 6,
    entity: 'employee',
    group: 'Nhân sự',
    endpoint: '/api/employees/summary',
    overviewKpis: ['headcount_end', 'turnover_rate'],
    load: async () => (await import('../pages/hr-headcount-report-page')).HrHeadcountReportPage,
  },
  {
    label: 'Tình hình nghỉ phép',
    description: 'Số đơn, ngày nghỉ đã duyệt/đang chờ, số người nghỉ, tỷ lệ từ chối-trả về.',
    path: appRoutes.report.leaveUsage,
    sourcePath: appRoutes.hr.leaveRequests,
    icon: CalendarOff,
    //  Khớp mục con «Đơn nghỉ phép» (cùng đường với mục cha «Nghỉ phép») và
    //  `require('leave_request', ...)` của `/api/leave-requests/summary`.
    //  ReportKey.LEAVE_USAGE (backend) = 7.
    key: 7,
    entity: 'leave_request',
    group: 'Nhân sự',
    endpoint: '/api/leave-requests/summary',
    overviewKpis: ['days_pending'],
    load: async () => (await import('../pages/leave-usage-report-page')).LeaveUsageReportPage,
  },
  {
    label: 'Quỹ phép năm',
    description: 'Được cấp, đã dùng, đang giữ chỗ, còn lại — theo loại nghỉ, công ty, phòng ban.',
    path: appRoutes.report.leaveBalance,
    sourcePath: appRoutes.hr.leaveBalances,
    icon: Wallet,
    //  ReportKey.LEAVE_BALANCE (backend) = 8.
    key: 8,
    entity: 'leave_balance',
    group: 'Nhân sự',
    endpoint: '/api/leave-balances/summary',
    overviewKpis: ['remaining'],
    load: async () => (await import('../pages/leave-balance-report-page')).LeaveBalanceReportPage,
  },
]
