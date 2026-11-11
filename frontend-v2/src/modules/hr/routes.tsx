import {
  Banknote,
  BriefcaseBusiness,
  Building,
  Building2,
  CalendarDays,
  DoorOpen,
  FilePen,
  FileSignature,
  CalendarOff,
  CalendarPlus,
  CalendarRange,
  Database,
  IdCard,
  LayoutDashboard,
  Network,
  ScrollText,
  Settings2,
  UserCheck,
  Users,
  Wallet,
} from 'lucide-react'

import { Navigate } from 'react-router-dom'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'
import { ProfileChangeRequestNavBadge } from './components/profile-change-request-nav-badge'
import { LegacyUserPermissionRedirect } from './pages/legacy-permission-redirect'
import { workScheduleNavItem, workScheduleRoutes } from './config/work-schedule-module-entries'

/** Phân hệ NHÂN SỰ — nhân viên, phòng ban, pháp nhân, phân quyền tài khoản. */
export const hrModule: ErpModule = {
  id: 'hr',
  title: 'Nhân sự',
  description: 'Nhân viên, phòng ban, pháp nhân và phân quyền tài khoản.',
  icon: Users,
  path: appRoutes.hr.root,
  accent: 'bg-rose-500/10 text-rose-600 dark:text-rose-400',
  enabled: true,
  entity: 'employee',

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.hr.root,
      icon: LayoutDashboard,
      end: true,
      // Không có quyền đọc khóa nào của phân hệ thì ẩn luôn Tổng quan —
      // cùng luật với Thu mua, xem procurement/routes.tsx.
      entities: ['employee', 'department', 'company', 'role'],
    },
    {
      label: 'Nhân sự',
      path: appRoutes.hr.employees,
      icon: IdCard,
      entity: 'employee',
      group: 'Danh mục',
    },
    {
      //  duoc-CR-676: duyệt ĐỀ NGHỊ SỬA HỒ SƠ do nhân viên tự khai ở Trang cá nhân. ⚠️ `entity` +
      //  `action: 'write'` ở đây LÀ hàng rào của route (gác điều hướng mặc định MỞ) cho cả
      //  `/hr/profile-change-requests/:id`; trang còn tự kiểm lại `employee.write`.
      label: 'Duyệt sửa hồ sơ',
      path: appRoutes.hr.profileChangeRequests,
      icon: FilePen,
      entity: 'employee',
      action: 'write',
      badge: ProfileChangeRequestNavBadge,
      group: 'Danh mục',
    },
    {
      //  duoc-CR-669: Sơ đồ tổ chức. ⚠️ `entity` ở đây LÀ hàng rào của route (gác
      //  điều hướng mặc định MỞ); backend `/api/org-chart` gác `employee.read` + phạm vi.
      label: 'Sơ đồ tổ chức',
      path: appRoutes.hr.orgChart,
      icon: Network,
      entity: 'employee',
      group: 'Danh mục',
    },
    //  ── Master (duoc-CR-712) ──────────────────────────────────────────────
    //  Gom các danh mục nền (phòng ban, công ty, chức vụ, mẫu HĐLĐ) vào một cụm sổ xuống cho menu gọn.
    //  ⚠️ Mỗi mục con GIỮ NGUYÊN `entity` / `manage` của mình: bộ gác route (`canAccessRoute`) duyệt cả
    //  mục con và khớp theo đường dẫn dài nhất, mục con xét trước mục cha — nên dời vào cụm không đổi
    //  quyền của màn nào. Mục cha hiện khi có ít nhất một mục con được phép.
    {
      label: 'Master',
      path: appRoutes.hr.departments,
      icon: Database,
      entities: ['department', 'company', 'job_position', 'labor_contract_template', 'setting'],
      group: 'Danh mục',
      matchPaths: [
        appRoutes.hr.companies,
        appRoutes.hr.jobPositions,
        appRoutes.hr.laborContractTemplates,
        appRoutes.hr.settings,
      ],
      children: [
        {
          label: 'Phòng ban',
          path: appRoutes.hr.departments,
          icon: Building,
          entity: 'department',
        },
        {
          label: 'Công ty',
          path: appRoutes.hr.companies,
          icon: Building2,
          entity: 'company',
        },
        {
          //  Danh mục CHỨC VỤ (duoc-CR-320) — nguồn của ô chọn "Vị trí / Chức vụ".
          //  `manage: true`: mọi vai trò đều ĐỌC được danh mục (ô chọn cần thế),
          //  nhưng vào màn quản lý thì chỉ người SỬA được — cùng luật với "Danh mục
          //  phòng họp". Không có nó thì cả công ty thấy một mục menu mở ra chỉ để
          //  nhìn, mọi nút đều xám.
          label: 'Chức vụ',
          path: appRoutes.hr.jobPositions,
          icon: BriefcaseBusiness,
          entity: 'job_position',
          manage: true,
        },
        {
          //  Mẫu HĐLĐ (.docx) theo pháp nhân. ⚠️ Mục menu khai `entity` LÀ hàng rào
          //  của route (gác điều hướng mặc định MỞ): thiếu mục này thì ai đăng nhập
          //  cũng gõ URL vào được. Trang còn tự kiểm `can(..., 'read')` một lần nữa.
          label: 'Mẫu hợp đồng',
          //  duoc-CR-643: mở trang mẫu NGAY TRONG Nhân sự (CR-629b từng nhảy sang Thiết lập văn bản của
          //  phân hệ Văn bản — người dùng bị đẩy khỏi Nhân sự). Mục này cũng là hàng rào cho cả
          //  `/hr/labor-contract-templates/*` (trình soạn, danh sách biến) vì gác khớp theo ranh giới `/`.
          path: appRoutes.hr.laborContractTemplates,
          icon: FileSignature,
          entity: 'labor_contract_template',
        },
        {
          //  duoc-CR-713: Cài đặt nhân sự (kiểu HR Settings của ERPNext). ⚠️ `entity` ở đây LÀ hàng rào của route
          //  (gác điều hướng mặc định MỞ); backend `/api/settings` gác `setting.read` / `setting.write`.
          label: 'Cài đặt nhân sự',
          path: appRoutes.hr.settings,
          icon: Settings2,
          entity: 'setting',
        },
      ],
    },
    //  ── Nghỉ phép (CR-259) ────────────────────────────────────────────────
    //  Submenu gồm 4 mục con trên sidebar bên trái:
    //   1. Đơn nghỉ phép (leaveRequests)
    //   2. Lịch nghỉ (leaveCalendar)
    //   3. Quỹ phép năm (leaveBalances)
    //   4. Chính sách nghỉ phép (tab Phân bổ + tab Chính sách, duoc-CR-750)
    //   5. Thiết lập (leaveTypes + holidays + leaveBlocks)
    {
      label: 'Nghỉ phép',
      path: appRoutes.hr.leaveRequests,
      icon: CalendarOff,
      entities: [
        'leave_request',
        'leave_comp_request',
        'leave_encashment',
        'leave_balance',
        'leave_type',
        'holiday',
      ],
      //  ⚠️ Phải khai `group`, kẻo mục rơi vào rổ KHÔNG NHÓM — rổ đó đứng trên
      //  cùng, không tiêu đề, và vốn chỉ dành cho "Tổng quan". Hai mục nghỉ phép
      //  / phòng họp nằm lửng ở đó đọc như phần đuôi của Tổng quan chứ không ra
      //  mục riêng (khách nêu 14/09/2026).
      group: 'Danh mục',
      matchPaths: [
        appRoutes.hr.leaveCompRequests,
        appRoutes.hr.leaveEncashments,
        appRoutes.hr.leaveCalendar,
        appRoutes.hr.leaveBalances,
        appRoutes.hr.leaveTypes,
        appRoutes.hr.holidays,
        appRoutes.hr.leaveBlocks,
        appRoutes.hr.leavePolicies,
        appRoutes.hr.leavePolicyAssignments,
      ],
      children: [
        {
          label: 'Đơn nghỉ phép',
          path: appRoutes.hr.leaveRequests,
          icon: CalendarOff,
          entity: 'leave_request',
        },
        {
          //  duoc-CR-715 phase C. Khóa `leave_comp_request` gác luôn cả `/new` và `/:id` (nằm dưới đường
          //  dẫn danh sách) — route thiếu mục menu gác là ai đăng nhập cũng vào.
          label: 'Nghỉ bù',
          path: appRoutes.hr.leaveCompRequests,
          icon: CalendarPlus,
          entity: 'leave_comp_request',
        },
        {
          //  duoc-CR-719. ⚠️ `entity` ở đây LÀ hàng rào của route (gác điều hướng mặc định MỞ) — gác luôn `/new`
          //  và `/:id` vì cả hai nằm dưới đường dẫn danh sách.
          label: 'Thanh toán nghỉ phép',
          path: appRoutes.hr.leaveEncashments,
          icon: Banknote,
          entity: 'leave_encashment',
        },
        {
          label: 'Lịch nghỉ',
          path: appRoutes.hr.leaveCalendar,
          icon: CalendarRange,
          entity: 'leave_request',
        },
        {
          label: 'Quỹ phép năm',
          path: appRoutes.hr.leaveBalances,
          icon: Wallet,
          entity: 'leave_balance',
        },
        {
          //  duoc-CR-750: màn gộp HAI TAB — Phân bổ (`leave_balance.write`) · Chính sách (`leave_type.write`) — thay
          //  mục "Phân bổ chính sách" (duoc-CR-717) và tab thứ tư của Thiết lập. ⚠️ Mục này LÀ hàng rào của route
          //  (gác điều hướng mặc định MỞ), nên phải hiện khi có ÍT NHẤT một trong hai quyền và tắt khi thiếu cả hai:
          //  `entities` = "bất kỳ khóa nào", `action: 'write'` áp cho TỪNG khóa (`module-visibility.entityAllowed`) —
          //  ra đúng `leave_balance.write || leave_type.write`, cùng luật hiện tab ở `utils/leave-policy-hub-tabs.ts`
          //  (bài kiểm canh hai luật bằng nhau). KHÔNG gác `read`: seed cấp `leave_balance.read` phạm vi "của tôi" cho
          //  MỌI nhân viên (đại ca chốt 03/11/2026). Không dùng `manage` vì nó mở cả người chỉ có `create`/`delete`
          //  trên quỹ phép, rộng hơn màn phân bổ cũ. Trang hàng loạt có mục ẩn riêng gác `leave_balance.write`;
          //  chi tiết / thêm gói (`/hr/leave-policies/*`) có mục ẩn riêng gác quản lý `leave_type`.
          label: 'Chính sách nghỉ phép',
          path: appRoutes.hr.leavePolicyAssignments,
          icon: ScrollText,
          entities: ['leave_balance', 'leave_type'],
          action: 'write',
          matchPaths: [appRoutes.hr.leavePolicyBulkAssign, appRoutes.hr.leavePolicies],
        },
        {
          label: 'Thiết lập',
          path: appRoutes.hr.leaveTypes,
          icon: CalendarDays,
          entities: ['leave_type', 'holiday'],
          manage: true,
          matchPaths: [appRoutes.hr.holidays, appRoutes.hr.leaveBlocks],
        },
      ],
    },
    {
      label: 'Lịch ngày lễ',
      path: appRoutes.hr.holidays,
      icon: CalendarDays,
      entity: 'holiday',
      manage: true,
      hidden: true,
    },
    //  duoc-CR-715: mục ẩn để ĐƯỜNG DẪN có gác quyền (route thiếu mục menu gác = ai đăng nhập cũng vào).
    //  Khóa `leave_type` — cùng "Thiết lập" nghỉ phép.
    {
      label: 'Ngày cấm nghỉ',
      path: appRoutes.hr.leaveBlocks,
      icon: CalendarOff,
      entity: 'leave_type',
      manage: true,
      hidden: true,
    },
    //  duoc-CR-717: hai mục ẩn làm hàng rào route. `/hr/leave-policies/*` (thêm gói, chi tiết gói, và đường cũ của
    //  danh sách — nay chuyển hướng về tab Chính sách, duoc-CR-750) gác quản lý `leave_type`; trang Phân bổ hàng loạt
    //  nằm DƯỚI `/hr/leave-policy-assignments` nhưng chỉ dành cho người GHI quỹ phép — mục ẩn dài hơn thắng (gác khớp
    //  đường dài nhất), nên người chỉ có `leave_type.write` (vào được màn gộp) không mở được trang đó.
    {
      label: 'Chi tiết chính sách nghỉ phép',
      path: appRoutes.hr.leavePolicies,
      icon: ScrollText,
      entity: 'leave_type',
      manage: true,
      hidden: true,
    },
    {
      label: 'Phân bổ hàng loạt',
      path: appRoutes.hr.leavePolicyBulkAssign,
      icon: UserCheck,
      entity: 'leave_balance',
      action: 'write',
      hidden: true,
    },
    //  ── Lịch làm việc (mẫu lịch tuần + gán lịch) — xem `work-schedule-module-entries.tsx`.
    workScheduleNavItem,
    //  ── Đặt phòng họp (duoc-CR-279) ───────────────────────────────────────
    //  Submenu gồm 3 mục con trên sidebar bên trái:
    //   1. Lịch phòng họp (roomCalendar)
    //   2. Phiếu đặt phòng (roomBookings)
    //   3. Danh mục phòng họp (meetingRooms — chỉ quản trị viên)
    {
      label: 'Đặt phòng họp',
      path: appRoutes.hr.roomCalendar,
      icon: DoorOpen,
      entities: ['room_booking', 'meeting_room'],
      //  Cùng lý do với "Nghỉ phép" ngay trên — xem ghi chú ở đó.
      group: 'Danh mục',
      matchPaths: [appRoutes.hr.roomBookings, appRoutes.hr.meetingRooms],
      children: [
        {
          label: 'Lịch phòng họp',
          path: appRoutes.hr.roomCalendar,
          icon: CalendarRange,
          entity: 'room_booking',
        },
        {
          label: 'Phiếu đặt phòng',
          path: appRoutes.hr.roomBookings,
          icon: DoorOpen,
          entity: 'room_booking',
        },
        {
          label: 'Danh mục phòng',
          path: appRoutes.hr.meetingRooms,
          icon: Building,
          entity: 'meeting_room',
          manage: true,
        },
      ],
    },
    //  "Phân quyền tài khoản" đã dời sang phân hệ QUẢN TRỊ (duoc-CR-396) — khai
    //  ai được làm gì là việc quản trị hệ thống, không phải nghiệp vụ nhân sự.
    //  Vì vậy menu Nhân sự không còn nhóm "Quản trị" nào.
  ],

  routes: [
    {
      path: appRoutes.hr.root,
      lazy: async () => ({
        Component: (await import('./pages/hr-dashboard-page')).HrDashboardPage,
      }),
    },
    {
      path: appRoutes.hr.employees,
      lazy: async () => ({
        Component: (await import('./pages/employee-list-page')).EmployeeListPage,
      }),
    },
    {
      path: appRoutes.hr.employeeDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/employee-detail-page')).EmployeeDetailPage,
      }),
    },
    {
      path: appRoutes.hr.profileChangeRequests,
      lazy: async () => ({
        Component: (await import('./pages/profile-change-request-list-page')).ProfileChangeRequestListPage,
      }),
    },
    {
      path: appRoutes.hr.profileChangeRequestDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/profile-change-request-detail-page')).ProfileChangeRequestDetailPage,
      }),
    },
    {
      path: appRoutes.hr.orgChart,
      lazy: async () => ({
        Component: (await import('./pages/org-chart-page')).OrgChartPage,
      }),
    },
    {
      path: appRoutes.hr.settings,
      lazy: async () => ({
        Component: (await import('./pages/hr-settings-page')).HrSettingsPage,
      }),
    },
    {
      path: appRoutes.hr.departments,
      lazy: async () => ({
        Component: (await import('./pages/department-list-page')).DepartmentListPage,
      }),
    },
    {
      path: appRoutes.hr.departmentDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/department-detail-page')).DepartmentDetailPage,
      }),
    },
    {
      path: appRoutes.hr.companies,
      lazy: async () => ({
        Component: (await import('./pages/company-list-page')).CompanyListPage,
      }),
    },
    {
      path: appRoutes.hr.companyDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/company-detail-page')).CompanyDetailPage,
      }),
    },
    //  ── Đường CŨ của Phân quyền tài khoản (duoc-CR-396) ───────────────────
    //  Màn đã dời sang `/system/permissions`. Giữ hai route chuyển tiếp vì
    //  `/hr/permissions` sống hơn một năm: người dùng lưu dấu trang, và địa chỉ
    //  đó còn nằm trong mấy chục thư thông báo đã gửi đi. Không có nó thì bấm
    //  vào là trang 404, không gợi ý được gì.
    {
      path: appRoutes.hr.permissionsLegacy,
      element: <Navigate to={appRoutes.system.permissions} replace />,
    },
    {
      //  ⚠️ Giữ nguyên `:userId` sang đường mới chứ đừng đá hết về trang danh
      //  sách: liên kết trong thư "đã cấp quyền cho bạn" trỏ thẳng vào MỘT tài
      //  khoản, quăng về danh sách là bắt người ta đi tìm lại.
      path: appRoutes.hr.userPermissionDetailLegacy(':userId'),
      element: <LegacyUserPermissionRedirect />,
    },

    //  ── Nghỉ phép (CR-259) ────────────────────────────────────────────────
    //  ⚠️ `/new` phải đứng TRƯỚC `/:id`: react-router khớp theo độ cụ thể nên
    //  thứ tự khai không quyết định, nhưng để cạnh nhau đúng thứ tự đọc thì
    //  người sau không phải tự kiểm chứng lại điều đó.
    {
      path: appRoutes.hr.leaveRequests,
      lazy: async () => ({
        Component: (await import('./pages/leave-request-list-page')).LeaveRequestListPage,
      }),
    },
    {
      path: appRoutes.hr.leaveRequestNew,
      lazy: async () => ({
        Component: (await import('./pages/leave-request-detail-page')).LeaveRequestDetailPage,
      }),
    },
    {
      path: appRoutes.hr.leaveRequestDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/leave-request-detail-page')).LeaveRequestDetailPage,
      }),
    },
    {
      path: appRoutes.hr.leaveCompRequests,
      lazy: async () => ({
        Component: (await import('./pages/leave-comp-request-list-page')).LeaveCompRequestListPage,
      }),
    },
    {
      path: appRoutes.hr.leaveCompRequestNew,
      lazy: async () => ({
        Component: (await import('./pages/leave-comp-request-detail-page'))
          .LeaveCompRequestDetailPage,
      }),
    },
    {
      path: appRoutes.hr.leaveCompRequestDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/leave-comp-request-detail-page'))
          .LeaveCompRequestDetailPage,
      }),
    },
    {
      path: appRoutes.hr.leaveEncashments,
      lazy: async () => ({
        Component: (await import('./pages/leave-encashment-list-page')).LeaveEncashmentListPage,
      }),
    },
    {
      path: appRoutes.hr.leaveEncashmentNew,
      lazy: async () => ({
        Component: (await import('./pages/leave-encashment-detail-page')).LeaveEncashmentDetailPage,
      }),
    },
    {
      path: appRoutes.hr.leaveEncashmentDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/leave-encashment-detail-page')).LeaveEncashmentDetailPage,
      }),
    },
    {
      path: appRoutes.hr.leaveCalendar,
      lazy: async () => ({
        Component: (await import('./pages/leave-calendar-page')).LeaveCalendarPage,
      }),
    },
    {
      path: appRoutes.hr.leaveBalances,
      lazy: async () => ({
        Component: (await import('./pages/leave-balance-page')).LeaveBalancePage,
      }),
    },
    {
      path: appRoutes.hr.leaveBalanceDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/leave-balance-detail-page')).LeaveBalanceDetailPage,
      }),
    },
    {
      path: appRoutes.hr.leaveTypes,
      lazy: async () => ({
        Component: (await import('./pages/leave-type-list-page')).LeaveTypeListPage,
      }),
    },
    {
      //  Trang THÊM MỚI dùng chính component chi tiết — nó nhận ra chế độ tạo
      //  bằng việc route này không có `:id`. Xem `CrudDetailPage`.
      path: appRoutes.hr.leaveTypeNew,
      lazy: async () => ({
        Component: (await import('./pages/leave-type-detail-page')).LeaveTypeDetailPage,
      }),
    },
    {
      path: appRoutes.hr.leaveTypeDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/leave-type-detail-page')).LeaveTypeDetailPage,
      }),
    },
    {
      path: appRoutes.hr.holidays,
      lazy: async () => ({
        Component: (await import('./pages/holiday-list-page')).HolidayListPage,
      }),
    },
    {
      path: appRoutes.hr.holidayNew,
      lazy: async () => ({
        Component: (await import('./pages/holiday-detail-page')).HolidayDetailPage,
      }),
    },
    {
      path: appRoutes.hr.leaveBlocks,
      lazy: async () => ({
        Component: (await import('./pages/leave-block-list-page')).LeaveBlockListPage,
      }),
    },
    {
      path: appRoutes.hr.leaveBlockNew,
      lazy: async () => ({
        Component: (await import('./pages/leave-block-detail-page')).LeaveBlockDetailPage,
      }),
    },
    //  ── Chính sách nghỉ phép (duoc-CR-717, gộp hai tab ở duoc-CR-750) ──────────────
    //  Hàng rào: mục "Chính sách nghỉ phép" (`leave_balance` hoặc `leave_type`, write), mục ẩn "Chi tiết chính
    //  sách nghỉ phép" (quản lý `leave_type`) và mục ẩn "Phân bổ hàng loạt" (`leave_balance.write`).
    {
      //  Đường CŨ của danh sách gói → tab Chính sách. Giữ cho dấu trang / HDSD / tin cũ.
      path: appRoutes.hr.leavePolicies,
      lazy: async () => ({
        Component: (await import('./pages/leave-policies-legacy-redirect')).LeavePoliciesLegacyRedirect,
      }),
    },
    {
      //  ⚠️ Phải đứng TRƯỚC `:id` — `CrudDetailPage` tự nhận ra chế độ thêm mới.
      path: appRoutes.hr.leavePolicyNew,
      lazy: async () => ({
        Component: (await import('./pages/leave-policy-detail-page')).LeavePolicyDetailPage,
      }),
    },
    {
      path: appRoutes.hr.leavePolicyDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/leave-policy-detail-page')).LeavePolicyDetailPage,
      }),
    },
    {
      //  Màn gộp hai tab — giữ đường của màn phân bổ cũ nên mọi link `?policy_id=` cũ vẫn mở đúng (tab Phân bổ là
      //  tab mặc định của người có quyền phân bổ).
      path: appRoutes.hr.leavePolicyAssignments,
      lazy: async () => ({
        Component: (await import('./pages/leave-policy-hub-page')).LeavePolicyHubPage,
      }),
    },
    {
      path: appRoutes.hr.leavePolicyBulkAssign,
      lazy: async () => ({
        Component: (await import('./pages/leave-policy-bulk-assign-page')).LeavePolicyBulkAssignPage,
      }),
    },
    //  ── Đặt phòng họp (duoc-CR-279) ───────────────────────────────────────
    {
      path: appRoutes.hr.roomCalendar,
      lazy: async () => ({
        Component: (await import('./pages/room-calendar-page')).RoomCalendarPage,
      }),
    },
    {
      path: appRoutes.hr.roomBookings,
      lazy: async () => ({
        Component: (await import('./pages/room-booking-list-page')).RoomBookingListPage,
      }),
    },
    {
      //  `/new` và `/:id` dùng CHUNG component — nó tự nhận ra chế độ đặt mới.
      path: appRoutes.hr.roomBookingNew,
      lazy: async () => ({
        Component: (await import('./pages/room-booking-detail-page')).RoomBookingDetailPage,
      }),
    },
    {
      path: appRoutes.hr.roomBookingDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/room-booking-detail-page')).RoomBookingDetailPage,
      }),
    },
    {
      path: appRoutes.hr.laborContractTemplates,
      lazy: async () => ({
        Component: (await import('./pages/labor-contract-template-list-page')).LaborContractTemplateListPage,
      }),
    },
    //  duoc-CR-630 — Danh sách biến của mẫu. Cũng nằm dưới `/hr/labor-contract-templates` nên chung hàng rào
    //  `labor_contract_template`; trang còn tự kiểm `can(..., 'read')`.
    {
      path: appRoutes.hr.laborContractVariables,
      lazy: async () => ({
        Component: (await import('./pages/labor-contract-variables-page')).LaborContractVariablesPage,
      }),
    },
    //  duoc-CR-606 — soạn nội dung mẫu trên web. Đường nằm DƯỚI mục menu "Mẫu hợp đồng" nên chung
    //  hàng rào `labor_contract_template` (gác điều hướng khớp theo ranh giới `/`).
    {
      path: appRoutes.hr.laborContractTemplateEditor(':id'),
      lazy: async () => ({
        Component: (await import('./pages/labor-contract-template-editor-page'))
          .LaborContractTemplateEditorPage,
      }),
    },
    {
      path: appRoutes.hr.jobPositions,
      lazy: async () => ({
        Component: (await import('./pages/job-position-list-page')).JobPositionListPage,
      }),
    },
    {
      //  ⚠️ Phải đứng TRƯỚC `:id` — cùng khuôn với `/hr/meeting-rooms/new`.
      //  Cùng một trang phục vụ hai vai: `CrudDetailPage` tự nhận ra mình đang
      //  ở `createRoute` và chuyển sang chế độ THÊM MỚI.
      path: appRoutes.hr.jobPositionNew,
      lazy: async () => ({
        Component: (await import('./pages/job-position-detail-page')).JobPositionDetailPage,
      }),
    },
    {
      path: appRoutes.hr.jobPositionDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/job-position-detail-page')).JobPositionDetailPage,
      }),
    },
    {
      path: appRoutes.hr.meetingRooms,
      lazy: async () => ({
        Component: (await import('./pages/meeting-room-list-page')).MeetingRoomListPage,
      }),
    },
    {
      path: appRoutes.hr.meetingRoomNew,
      lazy: async () => ({
        Component: (await import('./pages/meeting-room-detail-page')).MeetingRoomDetailPage,
      }),
    },
    {
      path: appRoutes.hr.meetingRoomDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/meeting-room-detail-page')).MeetingRoomDetailPage,
      }),
    },
    {
      path: appRoutes.hr.holidayDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/holiday-detail-page')).HolidayDetailPage,
      }),
    },
    {
      path: appRoutes.hr.leaveBlockDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/leave-block-detail-page')).LeaveBlockDetailPage,
      }),
    },
    ...workScheduleRoutes,
  ],
}
