import { ClipboardList } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ DỰ ÁN — chưa làm, hiện ở dạng "Sắp có".
 * Khi bắt đầu làm: tạo `pages/`, điền `nav` + `routes` rồi đổi `enabled: true`.
 */
export const projectModule: ErpModule = {
  id: 'project',
  title: 'Dự án',
  description: 'Kế hoạch, công việc và tiến độ dự án.',
  icon: ClipboardList,
  path: appRoutes.project.root,
  accent: 'bg-orange-500/10 text-orange-600 dark:text-orange-400',
  enabled: false,
  nav: [],
  routes: [],
}
