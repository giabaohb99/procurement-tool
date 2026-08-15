import { Settings } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ QUẢN TRỊ HỆ THỐNG — chưa làm, hiện ở dạng "Sắp có".
 * Sẽ gom tài khoản, vai trò, phân quyền, danh mục dùng chung và nhật ký thao tác.
 */
export const systemModule: ErpModule = {
  id: 'system',
  // Nhãn ngắn để không xuống dòng trong ô 112px; mô tả bên dưới nói rõ phạm vi.
  title: 'Quản trị',
  description: 'Tài khoản, vai trò, phân quyền và cấu hình.',
  icon: Settings,
  path: appRoutes.system.root,
  accent: 'bg-slate-100 text-slate-600',
  enabled: false,
  entity: 'setting',
  nav: [],
  routes: [],
}
