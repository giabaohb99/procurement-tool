import { Link, Outlet } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { env } from '@/core/config/env'
import { AssistantWidget } from '@/modules/assistant/components/assistant-widget'
import { appRoutes } from '@/shared/constants/app-routes'
import { NotificationBell } from '@/shared/notifications/notification-bell'
import { DemoAccountSwitcher } from './demo-account-switcher'
import { UserMenu } from './user-menu'

/**
 * Khung của màn CHỌN PHÂN HỆ: chỉ thanh trên, không menu trái.
 * Vào hẳn một phân hệ rồi thì đổi sang `ModuleLayout` (có sidebar).
 */
export function LauncherLayout() {
  const { can } = usePermission()
  return (
    /*
      `h-dvh` + `overflow-hidden`: khóa khung đúng một màn hình để phần cuộn nằm
      TRONG `<main>` bên dưới — giống hệt `ModuleLayout`.

      ⚠️ Đây là chốt chống lỗi trên ĐIỆN THOẠI, không phải chuyện bố cục. Bản cũ
      để **cửa sổ** cuộn và ghim thanh trên bằng `sticky top-0`. Trình duyệt iOS
      thu thanh công cụ của nó mỗi khi TÀI LIỆU cuộn xuống, mà lúc thu nó nuốt
      luôn phần trên khung nhìn và không đặt lại chỗ cho phần tử `sticky` cho tới
      khi buông tay — nên thanh trên biến mất, cuộn ngược lên mới thấy lại. Cho
      tài liệu đứng yên và cuộn ở `<main>` thì thanh công cụ không có cớ để thu,
      còn thanh trên thì không cần `sticky` nữa: nó nằm ngoài vùng cuộn.

      Kèm theo: `sticky top-0` của trang con (dải ô tìm) từ nay neo vào `<main>`,
      tức ngay dưới thanh trên — đừng cộng thêm chiều cao thanh trên vào `top`.
    */
    <div className="flex h-dvh flex-col overflow-hidden bg-canvas">
      <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-background px-4">
        <Link
          to={appRoutes.launcher}
          className="flex items-center transition-opacity hover:opacity-80"
          title="Về màn chọn phân hệ / Trang chủ"
        >
          <img src="/logo.svg" alt={env.appName} className="h-7 w-auto" />
        </Link>
        {/* Chuông có mặt ở CẢ HAI khung: việc cần xử lý không đợi người dùng
            vào hẳn một phân hệ mới được báo. */}
        <div className="flex items-center gap-1">
          <NotificationBell />
          {/*  Có mặt ở cả hai khung: người trình diễn hay đổi vai ngay từ màn
               chọn phân hệ, vì mỗi vai thấy một bộ phân hệ khác nhau. */}
          <DemoAccountSwitcher />
          <UserMenu />
        </div>
      </header>

      {/* `min-h-0` để `overflow-auto` có chiều cao xác định mà kích hoạt (item
          flex mặc định không co xuống dưới min-content của nội dung).
          `flex-col` để trang con canh giữa theo chiều dọc bằng `flex-1 justify-center`. */}
      <main className="flex min-h-0 flex-1 flex-col overflow-auto">
        <Outlet />
      </main>

      {/* Bong bóng Trợ lý AI cũng có mặt ở màn chọn phân hệ — chỉ ai có quyền mới thấy. */}
      {can('assistant', 'read') && <AssistantWidget />}
    </div>
  )
}
