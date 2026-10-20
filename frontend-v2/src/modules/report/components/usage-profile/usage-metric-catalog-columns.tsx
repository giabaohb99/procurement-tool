import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import type { DataTableColumn } from '@/shared/data-table'

import { USAGE_METRIC_DEFINITIONS } from '../../config/usage-metric-definitions'
import { metricLabel } from '../../config/usage-metric-labels'
import type { UsageMetricCatalogItem } from '../../types/usage-metric-catalog'
import { goodWhenLabel } from '../../utils/usage-metric-catalog-helpers'
import { UsageMetricStatusCell } from './usage-metric-status-cell'

/** Cột bảng của một nhóm chỉ số (bọc `useMemo` ở nơi dùng). */
export function buildUsageMetricCatalogColumns(hasWeek: boolean): DataTableColumn<UsageMetricCatalogItem>[] {
  return [
    {
      key: 'metric', header: 'Chỉ số', width: 200, hideable: false, wrap: true,
      cell: (r) => (
        <div className="min-w-0">
          <div className="font-medium">{metricLabel(r.key)}</div>
          <div className="text-xs text-muted-foreground">{r.key}</div>
        </div>
      ),
    },
    { key: 'meaning', header: 'Ý nghĩa', width: 260, wrap: true, cell: (r) => USAGE_METRIC_DEFINITIONS[r.key]?.meaning },
    { key: 'formula', header: 'Cách tính', width: 300, wrap: true, cell: (r) => USAGE_METRIC_DEFINITIONS[r.key]?.formula },
    { key: 'source', header: 'Nguồn dữ liệu', width: 220, wrap: true, cell: (r) => USAGE_METRIC_DEFINITIONS[r.key]?.source },
    { key: 'good', header: 'Tốt khi', width: 120, cell: (r) => goodWhenLabel(r.direction) },
    { key: 'status', header: 'Trạng thái', width: 220, wrap: true, cell: (r) => <UsageMetricStatusCell item={r} hasWeek={hasWeek} /> },
    {
      //  duoc-CR-650: chỉ số chưa ai đo được thì không có gì để xếp hạng.
      key: 'ranking', header: 'Xếp hạng', width: 140, hideable: false,
      cell: (r) =>
        r.measured_users > 0 ? (
          <Link className="text-primary underline-offset-2 hover:underline" to={appRoutes.report.usageProfilesByMetric(r.key)}>
            Xem xếp hạng
          </Link>
        ) : (
          <span className="text-muted-foreground" title="Chưa có người nào đo được chỉ số này nên chưa xếp hạng được">
            Chưa có dữ liệu
          </span>
        ),
    },
  ]
}
