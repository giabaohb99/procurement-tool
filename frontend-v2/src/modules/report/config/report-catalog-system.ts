import { UserSearch } from 'lucide-react'

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
    //  Không góp mặt ở dải KPI Tổng quan (số liệu cá nhân) — chỉ ở «Danh sách báo cáo».
    overviewKpis: [],
    load: async () => (await import('../pages/usage-profile-list-page')).UsageProfileListPage,
  },
]
