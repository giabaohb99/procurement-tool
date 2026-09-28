import { ChartColumn, LayoutDashboard } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

import { REPORT_CATALOG } from './config/report-catalog'

/**
 * Phân hệ BÁO CÁO — gom các trang báo cáo của từng phân hệ về một chỗ.
 *
 * Menu, route và thẻ lối tắt đều dựng từ `REPORT_CATALOG`; thêm báo cáo mới thì
 * sửa ở đó, đừng khai tay ở đây. Khóa quyền của từng mục lấy đúng khóa của mục
 * menu ở phân hệ gốc nên ai thấy báo cáo bên đó thì thấy bên này, không hơn.
 */
export const reportModule: ErpModule = {
  id: 'report',
  title: 'Báo cáo',
  description: 'Báo cáo của mọi phân hệ gom về một chỗ.',
  icon: ChartColumn,
  path: appRoutes.report.root,
  accent: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400',
  enabled: true,
  entity: 'report',

  nav: [
    {
      label: 'Tổng quan',
      path: appRoutes.report.root,
      icon: LayoutDashboard,
      end: true,
      // Không đọc được báo cáo nào thì Tổng quan cũng rỗng — ẩn luôn, kẻo thẻ
      // Báo cáo mở cho người không có gì để xem.
      entities: [...new Set(REPORT_CATALOG.map((r) => r.entity))],
    },
    ...REPORT_CATALOG.map((r) => ({
      label: r.label,
      path: r.path,
      icon: r.icon,
      entity: r.entity,
      group: r.group,
    })),
  ],

  routes: [
    {
      path: appRoutes.report.root,
      lazy: async () => ({
        Component: (await import('./pages/report-overview-page')).ReportOverviewPage,
      }),
    },
    ...REPORT_CATALOG.map((r) => ({
      path: r.path,
      lazy: async () => ({ Component: await r.load() }),
    })),
  ],
}
