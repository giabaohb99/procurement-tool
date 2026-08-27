import { ChartColumn } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ BÁO CÁO — chưa làm, hiện ở dạng "Sắp có".
 * Khi bắt đầu làm: tạo `pages/`, điền `nav` + `routes` rồi đổi `enabled: true`.
 */
export const reportModule: ErpModule = {
  id: 'report',
  title: 'Báo cáo',
  description: 'Báo cáo điều hành và số liệu tổng hợp.',
  icon: ChartColumn,
  path: appRoutes.report.root,
  accent: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400',
  enabled: false,
  entity: 'report',
  nav: [],
  routes: [],
}
