import { Link, useLocation } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'
import { LIST_SECTION_TABS_STICKY } from '../utils/list-sticky'

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

interface RoomSectionTabsProps {
  /**
   * Ghim dải tab lên đỉnh khung cuộn ở khổ điện thoại.
   *
   * ⚠️ Chỉ bật ở màn **không có hàng tab thứ hai** — tức Danh mục phòng họp.
   * Hai màn kia (Lịch · Phiếu đặt phòng) ghim hàng tab bên trong chúng
   * (`LIST_TABS_STICKY`) chứ không ghim dải này; ghim cả hai là hai dải chồng
   * nhau ăn 84px chiều cao trên một màn 844px. Cùng luật với `LeaveSectionTabs`.
   */
  sticky?: boolean
}

export function RoomSectionTabs({ sticky = false }: RoomSectionTabsProps) {
  const { can } = usePermission()
  const { pathname } = useLocation()

  const tabs = TABS.filter((tab) => tab.visible(can))
  //  Một tab thì không phải là tab — người dùng không chuyển đi đâu được.
  if (tabs.length <= 1) return null

  return (
    //  ⚠️ Khổ hẹp: dải này CHIA ĐỀU hết bề ngang, không co theo nội dung.
    //
    //  Ba nhãn dài gần bằng nhau nhưng không bằng hẳn (102 · 111 · 114px) và
    //  cộng lại vẫn hụt 23px so với lòng trang — xếp theo nội dung thì ra ba ô
    //  lệch nhau vài pixel rồi bỏ trống một khoảng bên phải, đọc ra là dựng ẩu
    //  (khách báo 09/09/2026).
    //
    //  ⚠️ Dải này giữ kiểu NÚT NỀN ĐẶC; hàng ba tab ngay bên dưới (`TabsList`
    //  của màn Phiếu đặt phòng) mới là hàng đổi sang gạch chân ở khổ hẹp — xem
    //  `list-tab-underline.ts`. Hai hàng cùng kiểu thì thành sáu ô giống hệt
    //  nhau thẳng cột, đọc ra như MỘT lưới 2×3 chứ không ra hai cấp điều hướng.
    //  Cấp trên là *đang ở màn nào* nên nó giữ phần nhấn mạnh.
    //
    //  Khác `LeaveSectionTabs` cố ý: bên đó BỐN tab, chia đều thì mỗi ô còn
    //  ~87px và nhãn phải cắt; nó chọn cuộn ngang. Ba tab thì không vướng.
    <nav
      className={cn(
        'flex shrink-0 flex-wrap items-center gap-1 pb-3',
        //  ⚠️ `w-full` và dải ghim LOẠI TRỪ nhau, đừng đặt cả hai.
        //
        //  Dải ghim mang `-mx-4 px-4` để nền phủ hết bề ngang khung; nó trông
        //  cậy vào việc khối tự giãn ra theo lề âm (thành 390px). `w-full` ghim
        //  cứng bề rộng bằng 100% khung cha (358px), nên khối bị **đẩy sang
        //  trái 16px mà không rộng thêm**: nền hụt 32px ở mép phải, và lòng
        //  trong tụt từ 358 xuống 326 — vừa đúng ngưỡng làm ba tab `flex-1`
        //  vỡ thành HAI HÀNG (đo được: 161 · 161 · 326). Không ghim thì `w-full`
        //  vẫn cần, vì lúc đó không có lề âm nào giãn khối ra.
        sticky ? LIST_SECTION_TABS_STICKY : 'max-md:w-full',
      )}
      aria-label="Các màn Đặt phòng"
    >
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
            //  Chữ và lề bóp lại ở khổ hẹp để **ba tab nằm trọn MỘT hàng**: cỡ
            //  cũ cho ra hai hàng trên máy 390px, và hàng thứ hai chỉ có đúng
            //  một tab lẻ loi — trông như một nút rơi ra khỏi cụm chứ không ra
            //  một dải chuyển màn.
            //
            //  `whitespace-nowrap` bắt buộc khi đã `flex-1` (cỡ gốc bằng 0):
            //  thiếu nó thì «Danh mục phòng» gãy làm hai dòng.
            className={cn(
              'rounded-md px-2 py-1.5 text-center text-xs font-medium whitespace-nowrap transition-colors max-md:flex-1 md:px-3 md:text-sm',
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
