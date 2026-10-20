import { ChartColumn, LayoutDashboard, ListChecks } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

import { REPORT_CATALOG } from './config/report-catalog'

/** `ReportKey.USAGE_PROFILE` (backend) = 14. */
const USAGE_PROFILE_REPORT_KEY = 14

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
      // Gác KÉP: hiện khi được gán XEM ÍT NHẤT MỘT báo cáo bất kỳ — union của cả
      // 13 khóa, đối xứng với `entities` ở trên (OR theo entity).
      reportKeys: REPORT_CATALOG.map((r) => r.key),
    },
    ...REPORT_CATALOG.map((r) => ({
      label: r.label,
      path: r.path,
      icon: r.icon,
      entity: r.entity,
      group: r.group,
      // Mỗi mục báo cáo gác thêm bằng đúng khóa của chính nó (`ReportKey` backend).
      reportKeys: [r.key],
    })),
    //  duoc-CR-644: «Bộ chỉ số đánh giá» — mục menu RIÊNG (route không có mục menu gác = mở cho mọi người). Không thêm
    //  vào REPORT_CATALOG vì trùng khóa 14 sẽ nhân đôi dòng ở tab «Báo cáo» của phân quyền; gác đúng như Hồ sơ cách làm việc.
    {
      label: 'Bộ chỉ số đánh giá',
      path: appRoutes.report.usageMetrics,
      icon: ListChecks,
      entity: 'setting' as const,
      group: 'Quản trị',
      reportKeys: [USAGE_PROFILE_REPORT_KEY],
    },
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
    //  Hồ sơ MỘT người: nằm DƯỚI đường của mục menu «Hồ sơ cách làm việc» để `canAccessRoute`
    //  (khớp tiền tố dài nhất) áp đúng khóa quyền + khóa báo cáo 14. Route không có mục menu gác = mở cho mọi người.
    {
      path: appRoutes.report.usageMetrics,
      lazy: async () => ({
        Component: (await import('./pages/usage-metric-catalog-page')).UsageMetricCatalogPage,
      }),
    },
    {
      path: appRoutes.report.usageProfileDetail(':userId'),
      lazy: async () => ({
        Component: (await import('./pages/usage-profile-detail-page')).UsageProfileDetailPage,
      }),
    },
  ],
}
