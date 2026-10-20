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
  ]
}
