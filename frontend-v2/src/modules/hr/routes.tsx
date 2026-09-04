import {
  Building,
  Building2,
  CalendarDays,
  CalendarOff,
  CalendarRange,
  IdCard,
  LayoutDashboard,
  ShieldCheck,
  Users,
  Wallet,
} from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

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
    //  ── Nghỉ phép (CR-259) ────────────────────────────────────────────────
    //  ⚠️ **MỘT mục menu cho cả năm màn** (04/09/2026). Trước đó là năm mục rời
    //  thành một nhóm riêng, chiếm gần nửa chiều cao menu Nhân sự — trong khi
    //  bốn trong năm màn là thứ mở vài lần một tháng. Nay chuyển qua lại bằng
    //  `LeaveSectionTabs` ngay trong trang.
    //
    //  Năm ĐƯỜNG DẪN giữ nguyên (xem docstring của `leave-section-tabs.tsx`),
    //  nên bốn màn kia vẫn khai đủ ở đây với `hidden: true` để **giữ khóa quyền
    //  riêng của từng màn** cho `canAccessRoute` — gõ thẳng `/hr/leave-types` mà
    //  không có quyền vẫn phải bị chặn tử tế.
    {
      label: 'Nghỉ phép',
      path: appRoutes.hr.leaveRequests,
      icon: CalendarOff,
      entity: 'leave_request',
      matchPaths: [
        appRoutes.hr.leaveCalendar,
        appRoutes.hr.leaveBalances,
        appRoutes.hr.leaveTypes,
        appRoutes.hr.holidays,
      ],
    },
    {
      label: 'Lịch nghỉ',
      path: appRoutes.hr.leaveCalendar,
      icon: CalendarRange,
      entity: 'leave_request',
      hidden: true,
    },
    {
      label: 'Quỹ phép năm',
      path: appRoutes.hr.leaveBalances,
      icon: Wallet,
      entity: 'leave_balance',
      hidden: true,
    },
    {
      label: 'Loại nghỉ',
      path: appRoutes.hr.leaveTypes,
      icon: CalendarDays,
      entity: 'leave_type',
      //  Sửa luật nghỉ là việc quản trị — chỉ người có quyền ghi mới vào được,
      //  chứ không mở cho mọi người rồi khóa từng nút bên trong. Cùng luật với
      //  tab «Thiết lập» trong `leave-section-tabs.tsx`.
      manage: true,
      hidden: true,
    },
    {
      label: 'Lịch ngày lễ',
      path: appRoutes.hr.holidays,
      icon: CalendarDays,
      entity: 'holiday',
      manage: true,
      hidden: true,
    },
    {
      label: 'Phân quyền tài khoản',
      path: appRoutes.hr.permissions,
      icon: ShieldCheck,
      entity: 'role',
      manage: true,
      group: 'Quản trị',
    },
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
    {
      path: appRoutes.hr.permissions,
      lazy: async () => ({
        Component: (await import('./pages/role-permission-page')).RolePermissionPage,
      }),
    },
    {
      path: appRoutes.hr.userPermissionDetail(':userId'),
      lazy: async () => ({
        Component: (await import('./pages/user-permission-detail-page'))
          .UserPermissionDetailPage,
      }),
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
    {
      path: appRoutes.hr.holidayDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/holiday-detail-page')).HolidayDetailPage,
      }),
    },
  ],
}
