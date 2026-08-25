import type { CSSProperties } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { canAccessRoute, canOpenModule } from '@/app/router/module-visibility'
import { useActiveModule } from '@/app/router/use-active-module'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { ForbiddenPage } from '@/shared/ui/forbidden-page'
import { SidebarInset, SidebarProvider } from '@/shared/ui/sidebar'
import { ModuleSidebar } from './module-sidebar'
import { ModuleTopbar } from './module-topbar'
import { useSidebarWidth } from './use-sidebar-width'

/**
 * Khung khi đã vào MỘT phân hệ: menu trái của phân hệ đó + thanh trên + nội dung.
 * Menu trái chỉ liệt kê màn hình của phân hệ đang mở; muốn sang phân hệ khác thì
 * bấm tên hệ thống ở đầu menu để về màn chọn phân hệ.
 */
export function ModuleLayout() {
  const activeModule = useActiveModule()
  const { pathname } = useLocation()
  const { can } = usePermission()
  const { width, setWidth } = useSidebarWidth()

  // URL không thuộc phân hệ nào (vd gõ tay đường dẫn sai) -> về màn chọn phân hệ.
  if (!activeModule) return <Navigate to={appRoutes.launcher} replace />

  // Không có mục nào trong phân hệ này -> không cho vào khung (khỏi thấy menu trống).
  // Gõ thẳng URL một phân hệ ngoài quyền cũng bị đá về màn chọn phân hệ (NF-20).
  if (!canOpenModule(activeModule, can)) return <Navigate to={appRoutes.launcher} replace />

  // Vào được phân hệ nhưng màn cụ thể ngoài quyền -> giữ khung + menu, ruột là 403
  // để người dùng chọn màn khác mình có quyền.
  const allowed = canAccessRoute(activeModule, pathname, can)

  return (
    // SidebarProvider lo trạng thái thu/mở, ngăn kéo mobile, phím tắt ⌘B và ghi
    // nhớ trạng thái vào cookie — không cần tự quản lý state.
    // `--sidebar-width` ghi đè mặc định 16rem bằng bề rộng người dùng đã kéo.
    <SidebarProvider
      // `h-svh` + `overflow-hidden`: khóa cả khung đúng một màn hình để phần
      // cuộn nằm TRONG `<main>` bên dưới. Thiếu nó thì khung của shadcn chỉ có
      // `min-h-svh` — trang dài làm khung dài theo, `overflow-auto` của `main`
      // không bao giờ kích hoạt và **cửa sổ** mới là chỗ cuộn. Hệ quả: mọi
      // `sticky top-0` bên trong `main` chết lặng (trình duyệt neo chúng vào
      // `main`, mà `main` thì không cuộn) — đó là lý do dải tiêu đề trang chi
      // tiết vẫn trôi lên mất.
      className="h-svh overflow-hidden"
      style={{ '--sidebar-width': `${width}px` } as CSSProperties}
    >
      <ModuleSidebar module={activeModule} onResizeWidth={setWidth} />
      {/*
        `min-w-0`: SidebarInset là item flex, mà item flex mặc định không co
        xuống dưới min-content của nội dung. Thiếu nó thì một bảng rộng bên
        trong sẽ nong cả khung ra, đẩy header và trang trôi ngang thay vì để
        bảng tự cuộn trong khung của nó.
      */}
      <SidebarInset className="min-w-0">
        <ModuleTopbar module={activeModule} />
        {/*
          `min-h-0` để khung có chiều cao xác định: trang danh sách dùng
          `<PageContainer fill>` (h-full) nên bảng cao bằng khung và tự cuộn bên
          trong, thanh phân trang luôn dính đáy.

          `overflow-auto` chứ không `overflow-hidden`: trang CHI TIẾT không dùng
          `fill`, nội dung dài hơn màn hình thì vẫn phải cuộn được.
        */}
        <main className="min-h-0 min-w-0 flex-1 overflow-auto bg-secondary">
          {allowed ? <Outlet /> : <ForbiddenPage />}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
