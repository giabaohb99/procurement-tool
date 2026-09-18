import { Link, useLocation } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'
import { LIST_SECTION_TABS_STICKY } from '../utils/list-sticky'

/**
 * Thanh chuyển màn của cụm NGHỈ PHÉP.
 *
 * ⚠️ Trước 04/09/2026 năm màn này là năm mục rời trong menu trái, và cụm đó
 * chiếm gần nửa chiều cao menu của phân hệ Nhân sự — trong khi bốn trong năm màn
 * là thứ mở vài lần một tháng. Nay gom về **một mục menu**, chuyển qua lại bằng
 * thanh tab này.
 *
 * ⚠️ **Giữ nguyên năm đường dẫn cũ**, tab chỉ là thanh điều hướng giữa chúng.
 * Gộp về một đường `?tab=…` thì link trong thư báo việc duyệt
 * (`/hr/leave-requests/{id}`, xem `task_notification.ENTITY_LINKS`) và mọi link
 * người dùng đã dán cho nhau đều gãy.
 *
 * ⚠️ Quyền chuyển từ MENU xuống ĐÂY. Menu cũ gác từng mục (`Quỹ phép` theo khóa
 * riêng, `Loại nghỉ` chỉ hiện với người sửa được); gộp một mục mà không mang
 * luật đó theo thì người thường nhìn thấy cả tab khai báo danh mục rồi bấm vào
 * ăn 403.
 */

interface SectionTab {
  label: string
  path: string
  /** Còn khớp khi đang ở những đường này — dùng cho tab gộp nhiều màn. */
  alsoMatch?: string[]
  visible: (can: ReturnType<typeof usePermission>['can']) => boolean
}

/** Hai màn con của tab «Thiết lập» trên sidebar. */
const SETTING_TABS: SectionTab[] = [
  {
    label: 'Loại nghỉ',
    path: appRoutes.hr.leaveTypes,
    visible: (can) => can('leave_type', 'write'),
  },
  {
    label: 'Lịch ngày lễ',
    path: appRoutes.hr.holidays,
    visible: (can) => can('holiday', 'write'),
  },
]

/** Đang đứng ở màn của tab này chưa — kể cả các đường con của nó. */
function isTabActive(tab: SectionTab, pathname: string): boolean {
  return pathname === tab.path || pathname.startsWith(`${tab.path}/`)
}

interface LeaveSectionTabsProps {
  sticky?: boolean
}

export function LeaveSectionTabs({ sticky = false }: LeaveSectionTabsProps) {
  const { can } = usePermission()
  const { pathname } = useLocation()

  const inSettings = SETTING_TABS.some((t) => pathname.startsWith(t.path))
  const settingTabs = SETTING_TABS.filter((t) => t.visible(can))

  // Chỉ hiện khi ở trong Thiết lập và có nhiều hơn 1 tab để chuyển qua lại
  if (!inSettings || settingTabs.length <= 1) return null

  return (
    <div className={cn('shrink-0 pb-3', sticky && LIST_SECTION_TABS_STICKY)}>
      <nav className="flex flex-wrap items-center gap-4 border-b" aria-label="Thiết lập nghỉ phép">
        {settingTabs.map((tab) => (
          <SubTabLink key={tab.path} to={tab.path} active={isTabActive(tab, pathname)}>
            {tab.label}
          </SubTabLink>
        ))}
      </nav>
    </div>
  )
}

function SubTabLink({
  to,
  children,
  active,
}: {
  to: string
  children: React.ReactNode
  active: boolean
}) {
  return (
    <Link
      to={to}
      aria-current={active ? 'page' : undefined}
      className={cn(
        //  `-mb-px` để gạch chân của tab đè lên đúng đường viền dưới của thanh,
        //  không nằm cách nó một pixel.
        '-mb-px border-b-2 px-1 pb-2 text-sm font-medium transition-colors',
        active
          ? 'border-primary text-foreground'
          : 'border-transparent text-muted-foreground hover:text-foreground',
      )}
    >
      {children}
    </Link>
  )
}
