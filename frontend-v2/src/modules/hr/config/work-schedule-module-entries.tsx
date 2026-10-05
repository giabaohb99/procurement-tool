import { CalendarClock, CalendarCog, CalendarDays, UserRoundCog } from 'lucide-react'
import type { RouteObject } from 'react-router-dom'

import type { ModuleNavItem } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Mục menu + route của «Lịch làm việc», tách khỏi `routes.tsx` (đã quá dài).
 *
 * ⚠️ Hai màn quản lý gác bằng `manage: true` trên entity `work_schedule`: mọi vai trò ĐỌC được
 * (form nghỉ phép cần), nhưng vào màn quản lý thì phải có tạo/sửa/xóa. Gác route
 * tính theo mục menu khớp tiền tố dài nhất (`canAccessRoute`) — mục thiếu là route
 * MỞ cho mọi người đăng nhập. Hai đường `/hr/work-schedules` và
 * `/hr/work-schedule-assignments` KHÔNG là con tiền tố của nhau nên mỗi đường có
 * mục menu riêng.
 */
export const workScheduleNavItem: ModuleNavItem = {
  label: 'Lịch làm việc',
  //  Cha trỏ vào «Xem lịch» (ai cũng có `employee.read` là vào được), không phải màn quản lý.
  //  Cha có con nên `itemAllowed` chỉ xét con: hiện khi CÓ ÍT NHẤT MỘT con được phép. Khai
  //  `entities` ở cha cho đúng nghĩa; KHÔNG khai `manage` ở cha nữa.
  path: appRoutes.hr.workRoster,
  icon: CalendarClock,
  entities: ['employee', 'work_schedule'],
  group: 'Danh mục',
  matchPaths: [appRoutes.hr.workSchedules, appRoutes.hr.workScheduleAssignments],
  children: [
    {
      label: 'Xem lịch',
      path: appRoutes.hr.workRoster,
      icon: CalendarDays,
      //  ⚠️ `employee` (đọc), KHÔNG `manage` và KHÔNG `work_schedule`: người xem lịch không cần quyền quản lý lịch.
      entity: 'employee',
    },
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
  ],
}

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
