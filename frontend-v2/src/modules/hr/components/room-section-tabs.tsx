import { Link, useLocation } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'

/**
 * Thanh chuyển màn của cụm ĐẶT PHÒNG HỌP — cùng khuôn với `LeaveSectionTabs`.
 *
 * Ba màn, **một mục menu**: xem lịch (mặc định), phiếu của tôi, danh mục phòng.
 * Khai ba mục menu rời cho một việc dùng vài lần một tuần là chiếm chỗ của
 * những thứ mở hằng ngày.
 *
 * ⚠️ Tab «Danh mục phòng» hỏi quyền **`write`**, không phải `read`: khai phòng
 * là việc quản trị. Hỏi `read` thì mọi người đều thấy tab rồi bấm vào ăn 403 —
 * cùng luật với tab «Thiết lập» của Nghỉ phép.
 */

interface SectionTab {
  label: string
  path: string
  visible: (can: ReturnType<typeof usePermission>['can']) => boolean
}

const TABS: SectionTab[] = [
  {
    label: 'Lịch đặt phòng',
    path: appRoutes.hr.roomCalendar,
    visible: (can) => can('room_booking', 'read'),
  },
  {
    label: 'Phiếu đặt phòng',
    path: appRoutes.hr.roomBookings,
    visible: (can) => can('room_booking', 'read'),
  },
  {
    label: 'Danh mục phòng',
    path: appRoutes.hr.meetingRooms,
    visible: (can) => can('meeting_room', 'write'),
  },
]

/** Đang đứng ở màn của tab này chưa — kể cả các đường con của nó. */
function isTabActive(tab: SectionTab, pathname: string): boolean {
  return pathname === tab.path || pathname.startsWith(`${tab.path}/`)
}

export function RoomSectionTabs() {
  const { can } = usePermission()
  const { pathname } = useLocation()

  const tabs = TABS.filter((tab) => tab.visible(can))
  //  Một tab thì không phải là tab — người dùng không chuyển đi đâu được.
  if (tabs.length <= 1) return null

  return (
    <nav className="flex shrink-0 flex-wrap items-center gap-1 pb-3" aria-label="Các màn Đặt phòng">
      {tabs.map((tab) => {
        const active = isTabActive(tab, pathname)
        return (
          <Link
            key={tab.path}
            to={tab.path}
            //  ⚠️ `Link` + tự tính `active`, KHÔNG dùng `NavLink`: `aria-current`
            //  của `NavLink` đè lên thuộc tính truyền vào, nên tab sáng theo luật
            //  riêng sẽ tô màu mà không nói ra cho trình đọc màn hình.
            aria-current={active ? 'page' : undefined}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              active
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-accent hover:text-foreground',
            )}
          >
            {tab.label}
          </Link>
        )
      })}
    </nav>
  )
}
