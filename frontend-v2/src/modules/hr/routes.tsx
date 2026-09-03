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
    //  Nhóm riêng, đặt TRƯỚC «Quản trị»: đơn nghỉ phép là việc của mọi người
    //  trong công ty, còn phân quyền là việc của một hai người.
    {
      label: 'Đơn nghỉ phép',
      path: appRoutes.hr.leaveRequests,
      icon: CalendarOff,
      entity: 'leave_request',
      group: 'Nghỉ phép',
    },
    {
      label: 'Lịch nghỉ',
      path: appRoutes.hr.leaveCalendar,
      icon: CalendarRange,
      entity: 'leave_request',
      group: 'Nghỉ phép',
    },
    {
      label: 'Quỹ phép năm',
      path: appRoutes.hr.leaveBalances,
      icon: Wallet,
      entity: 'leave_balance',
      group: 'Nghỉ phép',
    },
    {
      label: 'Loại nghỉ',
      path: appRoutes.hr.leaveTypes,
      icon: CalendarDays,
      entity: 'leave_type',
      //  Sửa luật nghỉ là việc quản trị — chỉ hiện với người có quyền ghi, chứ
      //  không hiện cho mọi người rồi khóa từng nút bên trong.
      manage: true,
      group: 'Nghỉ phép',
    },
    {
      label: 'Lịch ngày lễ',
      path: appRoutes.hr.holidays,
      icon: CalendarDays,
      entity: 'holiday',
      manage: true,
      group: 'Nghỉ phép',
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
      path: appRoutes.hr.holidayDetail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/holiday-detail-page')).HolidayDetailPage,
      }),
    },
  ],
}
