import {
  BriefcaseBusiness,
  Building,
  Building2,
  CalendarDays,
  DoorOpen,
  CalendarOff,
  CalendarRange,
  IdCard,
  LayoutDashboard,
  Users,
  Wallet,
} from 'lucide-react'

import { Navigate } from 'react-router-dom'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'
import { LegacyUserPermissionRedirect } from './pages/legacy-permission-redirect'

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
      label: 'Phòng ban',
      path: appRoutes.hr.departments,
      icon: Building,
      entity: 'department',
      group: 'Danh mục',
    },
    {
      label: 'Công ty',
      path: appRoutes.hr.companies,
      icon: Building2,
      entity: 'company',
      group: 'Danh mục',
    },
    {
      //  Danh mục CHỨC VỤ (duoc-CR-320) — nguồn của ô chọn «Vị trí / Chức vụ».
      //  `manage: true`: mọi vai trò đều ĐỌC được danh mục (ô chọn cần thế),
      //  nhưng vào màn quản lý thì chỉ người SỬA được — cùng luật với «Danh mục
      //  phòng họp». Không có nó thì cả công ty thấy một mục menu mở ra chỉ để
      //  nhìn, mọi nút đều xám.
      label: 'Chức vụ',
      path: appRoutes.hr.jobPositions,
      icon: BriefcaseBusiness,
      entity: 'job_position',
      manage: true,
      group: 'Danh mục',
    },
    //  ── Nghỉ phép (CR-259) ────────────────────────────────────────────────
    //  Submenu gồm 4 mục con trên sidebar bên trái:
    //   1. Đơn nghỉ phép (leaveRequests)
    //   2. Lịch nghỉ (leaveCalendar)
    //   3. Quỹ phép năm (leaveBalances)
    //   4. Thiết lập (leaveTypes + holidays)
    {
      label: 'Nghỉ phép',
      path: appRoutes.hr.leaveRequests,
      icon: CalendarOff,
      entities: ['leave_request', 'leave_balance', 'leave_type', 'holiday'],
      //  ⚠️ Phải khai `group`, kẻo mục rơi vào rổ KHÔNG NHÓM — rổ đó đứng trên
      //  cùng, không tiêu đề, và vốn chỉ dành cho «Tổng quan». Hai mục nghỉ phép
      //  / phòng họp nằm lửng ở đó đọc như phần đuôi của Tổng quan chứ không ra
      //  mục riêng (khách nêu 14/09/2026).
      group: 'Danh mục',
      matchPaths: [
        appRoutes.hr.leaveCalendar,
        appRoutes.hr.leaveBalances,
        appRoutes.hr.leaveTypes,
        appRoutes.hr.holidays,
      ],
      children: [
        {
          label: 'Đơn nghỉ phép',
          path: appRoutes.hr.leaveRequests,
          icon: CalendarOff,
          entity: 'leave_request',
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
          label: 'Thiết lập',
          path: appRoutes.hr.leaveTypes,
          icon: CalendarDays,
          entities: ['leave_type', 'holiday'],
          manage: true,
          matchPaths: [appRoutes.hr.holidays],
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
    //  ── Đặt phòng họp (duoc-CR-279) ───────────────────────────────────────
    //  MỘT mục menu cho ba màn (lịch · phiếu · danh mục phòng), chuyển bằng
    //  `RoomSectionTabs`. Cùng luật với cụm Nghỉ phép ngay trên.
    {
      label: 'Đặt phòng họp',
      path: appRoutes.hr.roomCalendar,
      icon: DoorOpen,
      entity: 'room_booking',
      //  Cùng lý do với «Nghỉ phép» ngay trên — xem ghi chú ở đó.
      group: 'Danh mục',
      matchPaths: [appRoutes.hr.roomBookings, appRoutes.hr.meetingRooms],
    },
    {
      label: 'Phiếu đặt phòng',
      path: appRoutes.hr.roomBookings,
      icon: DoorOpen,
      entity: 'room_booking',
      hidden: true,
    },
    {
      label: 'Danh mục phòng họp',
      path: appRoutes.hr.meetingRooms,
      icon: DoorOpen,
      entity: 'meeting_room',
      //  Khai phòng là việc quản trị — chỉ người SỬA được mới vào, cùng luật
      //  với tab «Danh mục phòng» trong `RoomSectionTabs`.
      manage: true,
      hidden: true,
    },
    //  «Phân quyền tài khoản» đã dời sang phân hệ QUẢN TRỊ (duoc-CR-396) — khai
    //  ai được làm gì là việc quản trị hệ thống, không phải nghiệp vụ nhân sự.
    //  Vì vậy menu Nhân sự không còn nhóm «Quản trị» nào.
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
  ],
}
