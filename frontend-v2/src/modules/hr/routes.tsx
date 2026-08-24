import { Building, Building2, IdCard, LayoutDashboard, ShieldCheck, Users } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/** Phân hệ NHÂN SỰ — nhân viên, phòng ban, pháp nhân, phân quyền tài khoản. */
export const hrModule: ErpModule = {
  id: 'hr',
  title: 'Nhân sự',
  description: 'Nhân viên, phòng ban, pháp nhân và phân quyền tài khoản.',
  icon: Users,
  path: appRoutes.hr.root,
  accent: 'bg-rose-50 text-rose-600',
  enabled: true,
  entity: 'employee',

  nav: [
    { label: 'Tổng quan', path: appRoutes.hr.root, icon: LayoutDashboard, end: true },
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
  ],
}
