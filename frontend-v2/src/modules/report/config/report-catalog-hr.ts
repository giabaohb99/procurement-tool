import {
  ArrowRightLeft,
  Banknote,
  BookUser,
  CalendarOff,
  ClipboardList,
  DoorOpen,
  FilePen,
  FileSignature,
  Gift,
  IdCard,
  Network,
  Scale,
  UserCheck,
  UserX,
  Wallet,
} from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportCatalogEntry } from './report-catalog'

/**
 * Nhóm NHÂN SỰ của danh mục báo cáo (phase 04) — Nhân sự (biến động & cơ cấu) ·
 * Nghỉ phép (tình hình nghỉ) · Quỹ phép năm · Hợp đồng lao động · Hồ sơ còn thiếu
 * (duoc-CR-686) · Sổ quản lý lao động · Mẫu 01/PLI (duoc-CR-687) · Quỹ lương · Phúc lợi & sự kiện ·
 * Cơ cấu quản lý · Điều chuyển & bổ nhiệm (duoc-CR-688) · Có mặt theo ngày ·
 * Yêu cầu sửa hồ sơ · Sử dụng phòng họp · Đối tượng cần chú ý theo luật (duoc-CR-689). Mỗi báo cáo = một `ReportPageConfig`
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
    //  Khớp mục con "Đơn nghỉ phép" (cùng đường với mục cha "Nghỉ phép") và
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
  {
    label: 'Sổ quản lý lao động',
    description: 'Sổ theo luật: mỗi người một dòng, mỗi pháp nhân một sheet; người còn thiếu thông tin bắt buộc.',
    path: appRoutes.report.laborRegister,
    sourcePath: appRoutes.hr.employees,
    icon: BookUser,
    //  ReportKey.LABOR_BOOK (backend) = 19.
    key: 19,
    entity: 'employee',
    group: 'Nhân sự',
    endpoint: '/api/labor-register/summary',
    //  Không góp mặt ở dải KPI Tổng quan: backend đòi thêm `employee_sensitive.read` +
    //  `labor_contract.read` trong service, người được giao báo cáo mà thiếu hai quyền đó sẽ
    //  thấy thẻ Tổng quan hỏng; sổ/mẫu là biểu mẫu nộp định kỳ, không phải số theo dõi hằng ngày.
    overviewKpis: [],
    load: async () => (await import('../pages/labor-register-report-page')).LaborRegisterReportPage,
  },
  {
    label: 'Báo cáo sử dụng lao động (01/PLI)',
    description: 'Mẫu 01/PLI nộp Sở Nội vụ (05/6, 05/12): tổng lao động, nữ, nhóm vị trí việc làm, loại HĐ.',
    path: appRoutes.report.laborUsageReport,
    sourcePath: appRoutes.hr.employees,
    icon: ClipboardList,
    //  ReportKey.LABOR_USAGE_REPORT (backend) = 20.
    key: 20,
    entity: 'employee',
    group: 'Nhân sự',
    endpoint: '/api/labor-usage-report/summary',
    //  Như Sổ quản lý lao động ở trên — không lên dải KPI Tổng quan.
    overviewKpis: [],
    load: async () => (await import('../pages/labor-usage-report-page')).LaborUsageReportPage,
  },
  {
    label: 'Quỹ lương theo pháp nhân',
    description: 'Quỹ lương = lương + phụ cấp nhập ở hồ sơ từng người (số hiện tại); chỉ hiện tổng theo pháp nhân, phòng ban; nhóm dưới 3 người bị che.',
    path: appRoutes.report.payrollFund,
    //  duoc-CR-693: số lấy từ ô lương hồ sơ nên gác `employee` (backend `require('employee', read|export)`),
    //  khớp luôn khóa của danh sách nhân sự — hết là ngoại lệ ở `report-catalog.test.ts`.
    sourcePath: appRoutes.hr.employees,
    icon: Banknote,
    //  ReportKey.PAYROLL_FUND (backend) = 21.
    key: 21,
    entity: 'employee',
    group: 'Nhân sự',
    endpoint: '/api/payroll-fund/summary',
    //  Không lên dải KPI Tổng quan: số lương là số nhạy cảm, trang Tổng quan hay được mở
    //  trước đám đông (họp giao ban) — ai được giao thì vào hẳn trang này mà xem.
    overviewKpis: [],
    load: async () => (await import('../pages/payroll-fund-report-page')).PayrollFundReportPage,
  },
  {
    label: 'Phúc lợi & sự kiện',
    description: 'Danh sách nhận quà theo dịp (8/3, 20/10, 1/6, Trung thu, Tết, sinh nhật…), kinh phí theo pháp nhân.',
    path: appRoutes.report.benefitAudience,
    sourcePath: appRoutes.hr.employees,
    icon: Gift,
    //  ReportKey.BENEFIT_AUDIENCE (backend) = 22.
    key: 22,
    entity: 'employee',
    group: 'Nhân sự',
    endpoint: '/api/benefit-audience/summary',
    //  Không lên dải KPI Tổng quan: số chỉ có nghĩa khi đã chọn dịp + nhập mức quà.
    overviewKpis: [],
    load: async () => (await import('../pages/benefit-audience-report-page')).BenefitAudienceReportPage,
  },
  {
    label: 'Cơ cấu quản lý',
    description: 'Số quản lý, cấp dưới bình quân, người chưa gán quản lý, quản lý quá ít hoặc quá nhiều cấp dưới.',
    path: appRoutes.report.managementSpan,
    sourcePath: appRoutes.hr.employees,
    icon: Network,
    //  ReportKey.MANAGEMENT_SPAN (backend) = 23.
    key: 23,
    entity: 'employee',
    group: 'Nhân sự',
    endpoint: '/api/management-span/summary',
    overviewKpis: ['unassigned_manager'],
    load: async () => (await import('../pages/management-span-report-page')).ManagementSpanReportPage,
  },
  {
    label: 'Điều chuyển & bổ nhiệm',
    description: 'Điều chuyển, bổ nhiệm, kiêm nhiệm, miễn nhiệm trong kỳ; dòng người giữa các phòng ban.',
    path: appRoutes.report.workMoves,
    sourcePath: appRoutes.hr.employees,
    icon: ArrowRightLeft,
    //  ReportKey.WORK_MOVES (backend) = 24.
    key: 24,
    entity: 'employee',
    group: 'Nhân sự',
    endpoint: '/api/work-moves/summary',
    overviewKpis: ['transfers', 'appoints'],
    load: async () => (await import('../pages/work-moves-report-page')).WorkMovesReportPage,
  },
  {
    label: 'Có mặt theo ngày',
    description: 'Người-ngày phải làm theo lịch, nghỉ theo đơn đã duyệt và có mặt; tỷ lệ có mặt, tỷ lệ vắng theo phòng.',
    path: appRoutes.report.attendance,
    sourcePath: appRoutes.hr.workRoster,
    icon: UserCheck,
    //  ReportKey.ATTENDANCE_DAILY (backend) = 26.
    key: 26,
    entity: 'employee',
    group: 'Nhân sự',
    endpoint: '/api/attendance-report/summary',
    //  Không lên dải KPI Tổng quan: backend chặn kỳ dài hơn 92 ngày (422) — trang Tổng quan chọn
    //  "Năm nay" là thẻ này hỏng trong khi mọi thẻ khác vẫn chạy.
    overviewKpis: [],
    load: async () => (await import('../pages/attendance-report-page')).AttendanceReportPage,
  },
  {
    label: 'Yêu cầu sửa hồ sơ',
    description: 'Đề nghị sửa hồ sơ trong kỳ: đang chờ, chờ quá 2 ngày, tỷ lệ từ chối, thời gian xử lý bình quân.',
    path: appRoutes.report.profileChanges,
    sourcePath: appRoutes.hr.profileChangeRequests,
    icon: FilePen,
    //  ReportKey.PROFILE_CHANGES (backend) = 27.
    key: 27,
    //  Backend gác `employee.write` (+ khóa báo cáo 27), cùng chốt màn Duyệt sửa hồ sơ — rà mã CR-689 S5.
    entity: 'employee',
    action: 'write',
    group: 'Nhân sự',
    endpoint: '/api/profile-change-report/summary',
    overviewKpis: ['pending_over_2d'],
    load: async () => (await import('../pages/profile-changes-report-page')).ProfileChangesReportPage,
  },
  {
    label: 'Sử dụng phòng họp',
    description: 'Lượt đặt, giờ đã đặt, tỷ lệ lấp đầy, đặt rồi hủy, số người dự so với sức chứa — theo phòng họp, khung giờ.',
    path: appRoutes.report.roomUsage,
    sourcePath: appRoutes.hr.roomBookings,
    icon: DoorOpen,
    //  ReportKey.ROOM_USAGE (backend) = 28.
    key: 28,
    entity: 'room_booking',
    group: 'Nhân sự',
    endpoint: '/api/room-usage/summary',
    overviewKpis: ['occupancy'],
    load: async () => (await import('../pages/room-usage-report-page')).RoomUsageReportPage,
  },
  {
    label: 'Đối tượng cần chú ý theo luật',
    description: 'Sắp đến tuổi nghỉ hưu trong 12 tháng, đang nghỉ thai sản, lao động nữ nuôi con dưới 12 tháng.',
    path: appRoutes.report.legalWatch,
    sourcePath: appRoutes.hr.employees,
    icon: Scale,
    //  ReportKey.LEGAL_WATCH (backend) = 29.
    key: 29,
    entity: 'employee',
    group: 'Nhân sự',
    endpoint: '/api/legal-watch/summary',
    //  Không lên dải KPI Tổng quan: backend đòi thêm `employee_sensitive.read` (ngày sinh, con
    //  nhỏ) — người được giao báo cáo mà thiếu quyền đó sẽ thấy thẻ Tổng quan hỏng (như khóa 19).
    overviewKpis: [],
    load: async () => (await import('../pages/legal-watch-report-page')).LegalWatchReportPage,
  },
]
