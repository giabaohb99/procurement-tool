import type { DataTableColumn } from '@/shared/data-table'

import type { CapabilityPersonRow, CapabilityStats, CapabilityTypeRow } from '../../types/work-capability'
import { NOT_ENOUGH_SAMPLES, formatDays, formatEstimateRatio, formatRework, typeLabel } from '../../utils/work-capability-format'
import { formatCount, formatRatio } from '../../utils/usage-format'

const num = (width = 110) => ({ width, align: 'right' as const, sortable: false })

/** Ô số: dưới ngưỡng mẫu thì hiện chữ "chưa đủ mẫu" (một lần ở ô đầu) thay vì số, để không ai đọc "—" thành 0. */
function stat(render: (r: CapabilityStats) => string) {
  return (r: CapabilityStats) =>
    r.below_threshold ? (
      <span className="text-xs text-muted-foreground">—</span>
    ) : (
      <span className="tabular-nums">{render(r)}</span>
    )
}

function sampleCell(r: CapabilityStats) {
  return (
    <span className="tabular-nums">
      {formatCount(r.n_done)}
      {r.below_threshold && <span className="ml-1 text-xs text-muted-foreground">({NOT_ENOUGH_SAMPLES})</span>}
      {r.n_estimated > 0 && (
        <span className="ml-1 text-xs text-muted-foreground" title="Phiếu xong nhưng mốc xong là ước tính — không tính vào các số bên cạnh">
          +{formatCount(r.n_estimated)} ước tính
        </span>
      )}
    </span>
  )
}

const statColumns = <T extends CapabilityStats>(): DataTableColumn<T>[] => [
  { key: 'n_done', header: 'Số xong', ...num(190), cell: sampleCell },
  { key: 'p50', header: 'Trung vị', ...num(), cell: stat((r) => formatDays(r.p50_days)) },
  { key: 'p90', header: 'P90', ...num(), cell: stat((r) => formatDays(r.p90_days)) },
  { key: 'max', header: 'Chậm nhất', ...num(), cell: stat((r) => formatDays(r.max_days)) },
  { key: 'rework', header: 'Làm lại / phiếu', ...num(130), cell: stat((r) => formatRework(r.rework_rate)) },
  { key: 'late', header: 'Trễ hạn', ...num(), defaultHidden: true, cell: stat((r) => formatRatio(r.late_rate)) },
  { key: 'est', header: 'Thực tế / ước lượng', ...num(150), defaultHidden: true, cell: stat((r) => formatEstimateRatio(r.est_ratio_p50)) },
]

/** Bảng 1: theo loại phiếu / loại việc. */
export function buildTypeColumns(): DataTableColumn<CapabilityTypeRow>[] {
  return [{ key: 'type', header: 'Loại phiếu / loại việc', hideable: false, wrap: true, cell: typeLabel }, ...statColumns<CapabilityTypeRow>()]
}

/** Bảng 2: theo người trong từng loại. */
export function buildPersonColumns(): DataTableColumn<CapabilityPersonRow>[] {
  return [
    { key: 'person', header: 'Người xử lý', hideable: false, wrap: true, cell: (r) => `${r.full_name}${r.employee_code ? ` (${r.employee_code})` : ''}` },
    { key: 'type', header: 'Loại phiếu / loại việc', wrap: true, cell: typeLabel },
    ...statColumns<CapabilityPersonRow>(),
  ]
}
