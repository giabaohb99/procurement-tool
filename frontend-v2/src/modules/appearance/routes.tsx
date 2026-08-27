import { Palette } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ GIAO DIỆN — mỗi người tự chọn bảng màu cho tài khoản của mình.
 *
 * CỐ Ý không khai `entity`: đây không phải dữ liệu nghiệp vụ mà là tuỳ chọn hiển
 * thị cá nhân, ai đăng nhập được thì đổi được phần của mình. Backend cũng gác
 * bằng `get_current_user` chứ không bằng `require(...)` — xem
 * `app/modules/user_preference/controller.py`.
 */
export const appearanceModule: ErpModule = {
  id: 'appearance',
  title: 'Giao diện',
  description: 'Chọn bảng màu và chế độ nền cho riêng bạn.',
  icon: Palette,
  path: appRoutes.appearance.root,
  accent: 'bg-fuchsia-500/10 text-fuchsia-600 dark:text-fuchsia-400',
  enabled: true,

  nav: [
    {
      label: 'Bảng màu',
      path: appRoutes.appearance.root,
      icon: Palette,
      end: true,
    },
  ],

  routes: [
    {
      path: appRoutes.appearance.root,
      lazy: async () => ({
        Component: (await import('./pages/appearance-page')).AppearancePage,
      }),
    },
  ],
}
