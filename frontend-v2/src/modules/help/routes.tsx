import { BookOpen } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { tokenStorage } from '@/core/api'
import { useAuthStore } from '@/core/auth/auth-store'
import { appConfig } from '@/core/config/app-config'

/**
 * Trung tâm Hướng dẫn sử dụng — KHÔNG phải màn hình trong app này mà là một app
 * riêng (`help-center/`, cổng 8082) dùng chung backend + tài khoản. Ở đây chỉ là
 * một ô trên màn chọn phân hệ, bấm vào mở tab mới.
 *
 * Vì vậy module này không khai `routes`/`nav`, và bị loại khỏi `moduleRegistry`
 * (xem `module-registry.ts`) để router không phải đăng ký gì.
 */
export const helpCenterModule: ErpModule = {
  id: 'help-center',
  title: 'Hướng dẫn sử dụng',
  description: 'Tài liệu hướng dẫn dùng hệ thống — mở ở tab mới.',
  icon: BookOpen,
  path: '',
  externalUrl: buildHelpCenterUrl,
  accent: 'bg-amber-50 text-amber-600',
  enabled: true,
  nav: [],
  routes: [],
}

/**
 * Khu người dùng của Help Center là CÔNG KHAI nên link thường không kèm gì.
 *
 * Riêng người có quyền ghi tài liệu (`help_article.write`) được "bàn giao" phiên
 * qua HASH `#t=…&r=…` để bên đó vào thẳng khu quản trị mà không phải đăng nhập
 * lại — hai app khác cổng nên không dùng chung localStorage. Hash không được
 * trình duyệt gửi lên server, và help-center xóa nó khỏi URL ngay khi nạp
 * (`help-center/src/auth/auth-context.tsx`).
 *
 * Không kèm token cho người dùng thường: khu công khai vốn không cần, đưa token
 * sang app khác chỉ để đó là thừa rủi ro.
 */
function buildHelpCenterUrl(): string {
  const base = appConfig.helpCenterUrl
  const permissions = useAuthStore.getState().user?.permissions
  if (!permissions?.help_article?.write) return base

  const accessToken = tokenStorage.getAccessToken()
  if (!accessToken) return base

  const refreshToken = tokenStorage.getRefreshToken()
  const handoff = new URLSearchParams({
    t: accessToken,
    ...(refreshToken ? { r: refreshToken } : {}),
  })
  return `${base}#${handoff.toString()}`
}
