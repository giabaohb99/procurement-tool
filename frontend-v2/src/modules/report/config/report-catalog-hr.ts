import { CalendarOff, FileSignature, IdCard, UserX, Wallet } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportCatalogEntry } from './report-catalog'

/**
 * Nhóm NHÂN SỰ của danh mục báo cáo (phase 04) — Nhân sự (biến động & cơ cấu) ·
 * Nghỉ phép (tình hình nghỉ) · Quỹ phép năm · Hợp đồng lao động · Hồ sơ còn thiếu
 * (duoc-CR-686). Mỗi báo cáo = một `ReportPageConfig`
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
  {
    label: 'Hợp đồng lao động',
    description: 'HĐ đang hiệu lực, sắp hết hạn, quá hạn mà vẫn đi làm, nhân sự chưa có HĐ.',
    path: appRoutes.report.laborContract,
    //  HĐLĐ không có màn danh sách riêng (nằm ở tab của hồ sơ nhân sự) nên nguồn là danh
    //  sách nhân sự — khóa gác báo cáo vẫn là `labor_contract` của `/api/labor-contracts/summary`
    //  (ngoại lệ có ghi ở `report-catalog.test.ts`).
    sourcePath: appRoutes.hr.employees,
    icon: FileSignature,
    //  ReportKey.LABOR_CONTRACT (backend) = 17.
    key: 17,
    entity: 'labor_contract',
    group: 'Nhân sự',
    endpoint: '/api/labor-contracts/summary',
    overviewKpis: ['expiring_30', 'overdue'],
    load: async () => (await import('../pages/labor-contract-report-page')).LaborContractReportPage,
  },
  {
    label: 'Hồ sơ & tài khoản còn thiếu',
    description: 'Hồ sơ đang làm còn thiếu thông tin, tài khoản chưa mở hoặc còn mở sau khi nghỉ.',
    path: appRoutes.report.hrProfileGaps,
    sourcePath: appRoutes.hr.employees,
    icon: UserX,
    //  ReportKey.HR_PROFILE_GAPS (backend) = 18.
    key: 18,
    entity: 'employee',
    group: 'Nhân sự',
    endpoint: '/api/employees/profile-gaps/summary',
    overviewKpis: ['complete_rate'],
    load: async () => (await import('../pages/hr-profile-gaps-report-page')).HrProfileGapsReportPage,
  },
]
