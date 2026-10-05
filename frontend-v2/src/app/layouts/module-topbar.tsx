import { Link, useLocation } from 'react-router-dom'

import type { ErpModule, ModuleNavItem } from '@/app/router/module-definition'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/shared/ui/breadcrumb'
import { NotificationBell } from '@/shared/notifications/notification-bell'
import { Separator } from '@/shared/ui/separator'
import { SidebarTrigger } from '@/shared/ui/sidebar'
import { cn } from '@/shared/utils/cn'
import { DemoAccountSwitcher } from './demo-account-switcher'
import { UserMenu } from './user-menu'

//  ⚠️ Khớp theo RANH GIỚI `/` (cùng luật menu trái), không `startsWith` trần:
//  trần thì `/report/purchase` nuốt luôn `/report/purchase-progress` và
//  breadcrumb ghi sai tên màn (thấy 26/09/2026).
function matchesPath(pathname: string, path: string, end?: boolean): boolean {
  return end ? pathname === path : pathname === path || pathname.startsWith(`${path}/`)
}

/** Mục menu có đang sáng không — ĐÚNG luật `module-sidebar.tsx` (đường của mục + `matchPaths`). */
function isNavItemActive(item: ModuleNavItem, pathname: string): boolean {
  return (
    matchesPath(pathname, item.path, item.end) ||
    Boolean(item.matchPaths?.some((path) => matchesPath(pathname, path)))
  )
}

/**
 * Mục con đang sáng trên menu trái — làm cấp thứ BA của breadcrumb.
 *
 * Chỉ xét mục con ĐƯỢC VẼ (bỏ `hidden`), y như menu trái: màn gom về một mục khác qua
 * `matchPaths` (vd bốn thẻ Biểu đồ · Doanh nghiệp · So sánh · Thuế gom về «Giá thị
 * trường») phải ghi đúng tên mục ĐANG SÁNG bên trái, không ghi tên thẻ ẩn của nó.
 */
function findActiveChild(item: ModuleNavItem, pathname: string): ModuleNavItem | undefined {
  return item.children?.find((child) => !child.hidden && isNavItemActive(child, pathname))
}

/**
 * Thanh trên trong phân hệ: nút thu/mở menu + đường dẫn (phân hệ › mục menu › mục
 * con) + tài khoản. Dùng breadcrumb thay vì mỗi tên màn hình để luôn biết đang đứng
 * ở phân hệ nào, và bấm được về trang tổng quan của phân hệ đó.
 *
 * Cấp thứ ba (03/10/2026) chỉ có khi mục menu có `children` — vd «Thu mua › Tra cứu
 * thị trường › Giá thị trường», «Nhân sự › Nghỉ phép › Lịch nghỉ».
 */
export function ModuleTopbar({ module }: { module: ErpModule }) {
  const { pathname } = useLocation()

  // Màn hình hiện tại = mục menu khớp URL, hoặc mục CHA của mục con đang khớp (đường
  // của mục con không nhất thiết nằm dưới đường của mục cha). Đang ở ngay trang gốc
  // phân hệ thì breadcrumb chỉ có một cấp.
  const current = module.nav.find(
    (item) => isNavItemActive(item, pathname) || Boolean(findActiveChild(item, pathname)),
  )
  const isModuleRoot = pathname === module.path
  //  Có cấp thứ hai không — quyết định luôn việc giấu cấp phân hệ ở khổ hẹp.
  const hasCurrent = !isModuleRoot && Boolean(current)
  //  Cấp thứ ba — mục con trùng tên mục cha thì thôi, khỏi lặp chữ.
  const activeChild = hasCurrent && current ? findActiveChild(current, pathname) : undefined
  const hasChild = Boolean(activeChild && activeChild.label !== current?.label)

  return (
    <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b border-border bg-background px-4">
      <SidebarTrigger className="-ml-1 text-muted-foreground hover:text-foreground" />
      <Separator orientation="vertical" className="mx-1 !h-4" />

      {/*  ⚠️ Đường dẫn CẮT BẰNG «…», không xuống dòng. `BreadcrumbList` của
           shadcn để `flex-wrap` sẵn, mà thanh này cao cố định `h-14`: trên máy
           390px phần chừa cho đường dẫn chỉ còn ~160px nên «Nhân sự › Loại nghỉ»
           gãy làm hai dòng chen trong một thanh một dòng — nhìn như thanh bị vỡ
           (khách báo 09/09/2026). `min-w-0` ở cả hai cấp là bắt buộc: thiếu nó
           thì phần tử flex không co xuống dưới bề rộng nội dung và `truncate`
           không bao giờ có dịp chạy.

           ⚠️ **Dưới `sm` thì cấp phân hệ GIẤU HẲN, không cắt bằng «…»** — miễn
           là còn cấp thứ hai để mà giấu. Bản đầu cho nó co lại (`shrink-[3]`) và
           kết quả là *«N… › Phân quyền tài …»*: dấu ba chấm tốn đúng bằng chỗ nó
           tiết kiệm mà chẳng nói được gì, lại còn ăn mất chỗ của cái tên duy
           nhất đáng đọc. Giấu đi thì tên MÀN HÌNH được trọn ~160px và hiện đủ
           chữ. Không mất mát gì: phân hệ đang được tô sáng sẵn ở menu trái.
           Đứng ở gốc phân hệ thì cấp đó là cấp DUY NHẤT — luôn giữ.

           `shrink-[3]` giữ lại cho khổ từ `sm` lên: chỗ đó rộng nên hai cấp cùng
           hiện, và khi hụt thì vẫn là tên phân hệ nhường trước. */}
      <Breadcrumb className="min-w-0 flex-1">
        <BreadcrumbList className="flex-nowrap">
          <BreadcrumbItem
            className={cn('min-w-0 shrink-[3]', hasCurrent && 'max-sm:hidden')}
          >
            {isModuleRoot ? (
              <BreadcrumbPage className="truncate font-medium text-navy" title={module.title}>
                {module.title}
              </BreadcrumbPage>
            ) : (
              <BreadcrumbLink asChild>
                <Link to={module.path} className="truncate" title={module.title}>
                  {module.title}
                </Link>
              </BreadcrumbLink>
            )}
          </BreadcrumbItem>

          {hasCurrent && current && (
            <>
              <BreadcrumbSeparator className="shrink-0 max-sm:hidden" />
              {/*  Có cấp ba thì cấp hai là LINK về mục cha (chỉ cấp cuối mới là
                   `aria-current="page"`), và ở khổ hẹp giấu luôn cấp hai — cùng lý do
                   giấu cấp phân hệ ở trên: dành trọn chỗ cho tên màn đang đứng. */}
              <BreadcrumbItem className={cn('min-w-0', hasChild && 'shrink-[2] max-sm:hidden')}>
                {hasChild ? (
                  <BreadcrumbLink asChild>
                    <Link to={current.path} className="truncate" title={current.label}>
                      {current.label}
                    </Link>
                  </BreadcrumbLink>
                ) : (
                  <BreadcrumbPage
                    className="truncate font-medium text-navy"
                    title={current.label}
                  >
                    {current.label}
                  </BreadcrumbPage>
                )}
              </BreadcrumbItem>
            </>
          )}

          {hasChild && activeChild && (
            <>
              <BreadcrumbSeparator className="shrink-0 max-sm:hidden" />
              <BreadcrumbItem className="min-w-0">
                <BreadcrumbPage
                  className="truncate font-medium text-navy"
                  title={activeChild.label}
                >
                  {activeChild.label}
                </BreadcrumbPage>
              </BreadcrumbItem>
            </>
          )}
        </BreadcrumbList>
      </Breadcrumb>

      {/*  `shrink-0`: cụm bên phải là nút bấm, co nó lại thì chuông với ảnh đại
           diện méo đi — chỗ phải nhường là chữ, và chữ đã biết tự cắt. */}
      <div className="ml-auto flex shrink-0 items-center gap-1">
        {/*  CR-215: hộp "Chờ tôi duyệt" đã gỡ — nội dung gom vào tab Việc cần làm
            của Trang cá nhân, thanh trên chỉ còn một cái chuông. */}
        <NotificationBell />
        {/*  Chỉ hiện ở bản DEV — tự trả về null khi build thật. */}
        <DemoAccountSwitcher />
        <UserMenu />
      </div>
    </header>
  )
}
