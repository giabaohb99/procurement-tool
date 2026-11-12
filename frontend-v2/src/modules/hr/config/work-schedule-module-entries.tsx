import { CalendarClock, CalendarCog, UserRoundCog } from 'lucide-react'
import type { RouteObject } from 'react-router-dom'

import type { ModuleNavItem } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Mục menu + route của "Lịch làm việc", tách khỏi `routes.tsx` (đã quá dài).
 *
 * ⚠️ Hai màn quản lý gác bằng `manage: true` trên entity `work_schedule`: mọi vai trò ĐỌC được
 * (form nghỉ phép cần), nhưng vào màn quản lý thì phải có tạo/sửa/xóa. Gác route
 * tính theo mục menu khớp tiền tố dài nhất (`canAccessRoute`) — mục thiếu là route
 * MỞ cho mọi người đăng nhập. Hai đường `/hr/work-schedules` và
 * `/hr/work-schedule-assignments` KHÔNG là con tiền tố của nhau nên mỗi đường có
 * mục menu riêng.
 *
 * duoc-CR-754: hai màn quản lý (Mẫu lịch tuần, Gán lịch) dời vào cụm **Thiết lập** của menu
 * (`hr-setup-nav-item.tsx`); ở nhóm Nghiệp vụ chỉ còn một mục Xem lịch, không sổ xuống.
 */
export const workScheduleNavItem: ModuleNavItem = {
  label: 'Lịch làm việc',
  path: appRoutes.hr.workRoster,
  icon: CalendarClock,
  //  ⚠️ `employee` (đọc), KHÔNG `manage` và KHÔNG `work_schedule`: người xem lịch không cần quyền quản lý lịch.
  //  Mục này LÀ hàng rào của `/hr/work-roster` (gác điều hướng mặc định MỞ).
  entity: 'employee',
}

/** Hai màn quản lý lịch — con của cụm Thiết lập. Mỗi đường một mục vì không là tiền tố của nhau. */
export const workScheduleSetupNavItems: ModuleNavItem[] = [
  {
    label: 'Mẫu lịch tuần',
    path: appRoutes.hr.workSchedules,
    icon: CalendarCog,
    entity: 'work_schedule',
    manage: true,
  },
  {
    label: 'Gán lịch',
    path: appRoutes.hr.workScheduleAssignments,
    icon: UserRoundCog,
    entity: 'work_schedule',
    manage: true,
  },
]

export const workScheduleRoutes: RouteObject[] = [
  {
    path: appRoutes.hr.workRoster,
    lazy: async () => ({
      Component: (await import('../pages/work-roster-page')).WorkRosterPage,
    }),
  },
  {
    path: appRoutes.hr.workSchedules,
    lazy: async () => ({
      Component: (await import('../pages/work-schedule-list-page')).WorkScheduleListPage,
    }),
  },
  {
    //  Trang THÊM MỚI dùng chính component chi tiết (route tĩnh, không `:id`).
    path: appRoutes.hr.workScheduleNew,
    lazy: async () => ({
      Component: (await import('../pages/work-schedule-detail-page')).WorkScheduleDetailPage,
    }),
  },
  {
    path: appRoutes.hr.workScheduleDetail(':id'),
    lazy: async () => ({
      Component: (await import('../pages/work-schedule-detail-page')).WorkScheduleDetailPage,
    }),
  },
  {
    path: appRoutes.hr.workScheduleAssignments,
    lazy: async () => ({
      Component: (await import('../pages/work-schedule-assignment-list-page'))
        .WorkScheduleAssignmentListPage,
    }),
  },
]
