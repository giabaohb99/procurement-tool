import { Gauge, MousePointerClick, UserSearch } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportCatalogEntry } from './report-catalog'

/** Nhóm QUẢN TRỊ của danh mục báo cáo (duoc-CR-641) — Hồ sơ cách làm việc, chỉ admin xem mặc định. */
export const SYSTEM_REPORT_CATALOG: ReportCatalogEntry[] = [
  {
    label: 'Hồ sơ cách làm việc',
    description:
      'Nhịp làm việc, màn hay vào, cách làm phiếu và kiểu làm việc của từng người — chỉ quản trị.',
    path: appRoutes.report.usageProfiles,
    sourcePath: appRoutes.system.logs,
    icon: UserSearch,
    //  ReportKey.USAGE_PROFILE (backend) = 14.
    key: 14,
    entity: 'setting',
    group: 'Quản trị',
    endpoint: '/api/usage-profiles/summary',
    //  Không góp mặt ở dải KPI Tổng quan (số liệu cá nhân) — chỉ ở "Danh sách báo cáo".
    overviewKpis: [],
    load: async () => (await import('../pages/usage-profile-list-page')).UsageProfileListPage,
  },
  {
    label: 'Mức dùng chức năng',
    description:
      'Chức năng nào nhiều người dùng, chức năng nào không ai dùng, biểu mẫu nào hay bỏ dở, màn nào hay lỗi — gom theo phòng ban, không theo từng người.',
    path: appRoutes.report.featureUsage,
    sourcePath: appRoutes.system.logs,
    icon: MousePointerClick,
    //  ReportKey.FEATURE_USAGE (backend) = 15. Khóa RIÊNG để sau này mở cho người phụ trách sản phẩm mà không mở hồ sơ cá nhân (14).
    key: 15,
    entity: 'setting',
    group: 'Quản trị',
    endpoint: '/api/feature-usage/summary',
    overviewKpis: [],
    load: async () => (await import('../pages/feature-usage-report-page')).FeatureUsageReportPage,
  },
  {
    label: 'Năng lực theo loại việc',
    description:
      'Mỗi loại phiếu / loại việc mất bao lâu, bao nhiêu phần trăm phải làm lại, ai đang ôm bao nhiêu việc — chỉ dùng tham khảo, không chấm điểm.',
    path: appRoutes.report.workCapability,
    sourcePath: appRoutes.system.logs,
    icon: Gauge,
    //  ReportKey.WORK_CAPABILITY (backend) = 16. Số theo TỪNG NGƯỜI nên khóa riêng, mặc định chỉ admin.
    key: 16,
    entity: 'setting',
    group: 'Quản trị',
    endpoint: '/api/work-capability/summary',
    overviewKpis: [],
    load: async () => (await import('../pages/work-capability-report-page')).WorkCapabilityReportPage,
  },
]
