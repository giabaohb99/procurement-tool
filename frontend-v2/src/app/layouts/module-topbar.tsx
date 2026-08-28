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

  return (
    <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b border-border bg-background px-4">
      <SidebarTrigger className="-ml-1 text-muted-foreground hover:text-foreground" />
      <Separator orientation="vertical" className="mx-1 !h-4" />

      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            {isModuleRoot ? (
              <BreadcrumbPage className="font-medium text-navy">
                {module.title}
              </BreadcrumbPage>
            ) : (
              <BreadcrumbLink asChild>
                <Link to={module.path}>{module.title}</Link>
              </BreadcrumbLink>
            )}
          </BreadcrumbItem>

          {!isModuleRoot && current && (
            <>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage className="font-medium text-navy">
                  {current.label}
                </BreadcrumbPage>
              </BreadcrumbItem>
            </>
          )}
        </BreadcrumbList>
      </Breadcrumb>

      <div className="ml-auto flex items-center gap-1">
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
