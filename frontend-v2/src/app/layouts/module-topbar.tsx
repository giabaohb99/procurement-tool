import { Link, useLocation } from 'react-router-dom'

import type { ErpModule } from '@/app/router/module-definition'
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

/**
 * Thanh trên trong phân hệ: nút thu/mở menu + đường dẫn (phân hệ › màn hình) +
 * tài khoản. Dùng breadcrumb thay vì mỗi tên màn hình để luôn biết đang đứng ở
 * phân hệ nào, và bấm được về trang tổng quan của phân hệ đó.
 */
export function ModuleTopbar({ module }: { module: ErpModule }) {
  const { pathname } = useLocation()

  // Màn hình hiện tại = mục menu khớp URL. Đang ở ngay trang gốc phân hệ thì
  // breadcrumb chỉ có một cấp.
  const current = module.nav.find((item) =>
    item.end ? pathname === item.path : pathname.startsWith(item.path),
  )
  const isModuleRoot = pathname === module.path
  //  Có cấp thứ hai không — quyết định luôn việc giấu cấp phân hệ ở khổ hẹp.
  const hasCurrent = !isModuleRoot && Boolean(current)

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
              <BreadcrumbItem className="min-w-0">
                <BreadcrumbPage
                  className="truncate font-medium text-navy"
                  title={current.label}
                >
                  {current.label}
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
