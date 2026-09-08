import { Link, useLocation } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'

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

const TABS: SectionTab[] = [
  {
    label: 'Đơn nghỉ phép',
    path: appRoutes.hr.leaveRequests,
    visible: (can) => can('leave_request', 'read'),
  },
  {
    label: 'Lịch nghỉ',
    path: appRoutes.hr.leaveCalendar,
    visible: (can) => can('leave_request', 'read'),
  },
  {
    label: 'Quỹ phép năm',
    path: appRoutes.hr.leaveBalances,
    visible: (can) => can('leave_balance', 'read'),
  },
  {
    //  Gộp hai danh mục vào một tab: sửa luật nghỉ và khai lịch lễ là việc làm
    //  vài lần một năm, không đứng ngang hàng với việc mở hằng ngày.
    label: 'Thiết lập',
    path: appRoutes.hr.leaveTypes,
    alsoMatch: [appRoutes.hr.holidays],
    //  `write` chứ không `read`: chỉ hiện với người SỬA được luật, đúng như mục
    //  menu cũ (`manage: true`).
    visible: (can) => can('leave_type', 'write') || can('holiday', 'write'),
  },
]

/** Hai màn con của tab «Thiết lập» — hiện thành hàng tab thứ hai. */
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
  return [tab.path, ...(tab.alsoMatch ?? [])].some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  )
}

export function LeaveSectionTabs() {
  const { can } = usePermission()
  const { pathname } = useLocation()

  const tabs = TABS.filter((t) => t.visible(can))
  const inSettings = SETTING_TABS.some((t) => pathname.startsWith(t.path))
  const settingTabs = SETTING_TABS.filter((t) => t.visible(can))

  //  Một tab thì không phải là tab — người dùng không chuyển đi đâu được.
  if (tabs.length <= 1 && !inSettings) return null

  return (
    <div className="shrink-0 space-y-2 pb-3">
      <nav className="flex flex-wrap items-center gap-1" aria-label="Các màn Nghỉ phép">
        {tabs.map((tab) => (
          <TabLink key={tab.path} to={tab.path} active={isTabActive(tab, pathname)}>
            {tab.label}
          </TabLink>
        ))}
      </nav>

      {/*  Hàng tab thứ hai chỉ hiện khi đang trong «Thiết lập». Kiểu dáng khác
           hẳn hàng trên (chữ + gạch chân, không phải nút nền đặc) để hai cấp
           không đọc thành một dãy tab dài. */}
      {inSettings && settingTabs.length > 1 && (
        <nav className="flex flex-wrap items-center gap-4 border-b" aria-label="Thiết lập nghỉ phép">
          {settingTabs.map((tab) => (
            <SubTabLink key={tab.path} to={tab.path} active={isTabActive(tab, pathname)}>
              {tab.label}
            </SubTabLink>
          ))}
        </nav>
      )}
    </div>
  )
}

/**
 * ⚠️ `Link` + tự tính `active`, KHÔNG dùng `NavLink`.
 *
 * `NavLink` tự gắn `aria-current="page"` theo phép so đường của RIÊNG nó, và
 * `aria-current` của nó đè lên mọi thuộc tính truyền vào. Tab «Thiết lập» sáng
 * theo `alsoMatch` (đang ở màn Lịch ngày lễ) thì mắt thấy nó là tab đang mở
 * nhưng trình đọc màn hình lại không — tô màu mà không nói ra là hai người dùng
 * hai loại thiết bị đọc được hai thứ khác nhau.
 */
function TabLink({
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
        'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
        active
          ? 'bg-primary text-primary-foreground'
          : 'text-muted-foreground hover:bg-accent hover:text-foreground',
      )}
    >
      {children}
    </Link>
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
