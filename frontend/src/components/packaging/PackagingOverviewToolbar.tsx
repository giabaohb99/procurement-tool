import type { PackagingOverviewCounts, PackagingOverviewTrend } from '../../api/packaging-cost-types'
import type { ImpactAdvancedFilters } from '../../utils/packaging-impact-filters'
import { OVERVIEW_TREND_CHIPS, overviewChipLabel } from '../../utils/packaging-overview'
import PackagingFilterChipBar from './PackagingFilterChipBar'
import './packaging.css'

/**
 * Thanh lọc của màn Tổng hợp theo sản phẩm (duoc-CR-784): ô tìm + nút "Thêm điều kiện" + chip điều kiện (thanh lọc chung
 * `PackagingFilterChipBar`) và chip xu hướng KÈM SỐ ĐẾM (người chủ chốt không thích thẻ KPI to). Xu hướng giữ chip đếm riêng
 * nên menu "Thêm điều kiện" của màn này không có mục Xu hướng. Số đếm là của tập đã lọc theo từ khóa và điều kiện nhưng chưa
 * lọc xu hướng nên chip nào cũng hiện đủ số; bấm chip đang chọn lần nữa không bỏ chọn (muốn bỏ thì bấm "Tất cả").
 *
 * Đặt làm con của `TableToolbar` để hàng một cùng nút Cột / Tải lại; chip điều kiện nằm hàng dưới. "Xóa lọc" xóa cả từ khóa,
 * chip xu hướng lẫn mọi điều kiện.
 */
export default function PackagingOverviewToolbar({
  keyword, onKeyword, trend, onTrend, counts, advanced, onAdvanced, filtersActive, onReset,
}: {
  keyword: string
  onKeyword: (v: string) => void
  trend: PackagingOverviewTrend
  onTrend: (v: PackagingOverviewTrend) => void
  counts: PackagingOverviewCounts | undefined
  /** Bộ lọc nâng cao đang áp. */
  advanced: ImpactAdvancedFilters
  onAdvanced: (v: ImpactAdvancedFilters) => void
  /** Có bộ lọc nào đang bật (tìm, chip xu hướng hoặc điều kiện) → hiện "Xóa lọc". */
  filtersActive: boolean
  onReset: () => void
}) {
  return (
    <PackagingFilterChipBar variant="overview" value={advanced} onChange={onAdvanced} keyword={keyword} onKeyword={onKeyword}>
      <div className="pkg-pills" role="group" aria-label="Lọc theo xu hướng chi phí">
        {OVERVIEW_TREND_CHIPS.map((c) => (
          <button key={c.value} type="button" title={c.title} className={'pkg-pill' + (trend === c.value ? ' on' : '')}
            aria-pressed={trend === c.value} onClick={() => onTrend(c.value)}>{overviewChipLabel(c, counts)}</button>
        ))}
      </div>
      {filtersActive && <button type="button" className="btn ghost sm" onClick={onReset}><i className="ti ti-rotate" />Xóa lọc</button>}
    </PackagingFilterChipBar>
  )
}
