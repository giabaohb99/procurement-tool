import type { PackagingOverviewCounts, PackagingOverviewTrend } from '../../api/packaging-cost-types'
import type { ImpactAdvancedFilters } from '../../utils/packaging-impact-filters'
import { OVERVIEW_TREND_CHIPS, overviewChipLabel } from '../../utils/packaging-overview'
import PackagingImpactAdvancedFilter from './PackagingImpactAdvancedFilter'
import './packaging.css'

/**
 * Thanh lọc của màn Tổng hợp theo sản phẩm: ô tìm + chip xu hướng KÈM SỐ ĐẾM (người chủ chốt không thích thẻ KPI to) +
 * nút Lọc nâng cao. Số đếm là của tập đã lọc theo từ khóa và lọc nâng cao nhưng chưa lọc xu hướng nên chip nào cũng hiện đủ số.
 *
 * Đặt làm con của `TableToolbar` để MỘT HÀNG cùng nút Cột / Tải lại (người chủ báo 25/11/2026: hàng thứ hai chỉ có hai nút
 * lệch phải, chừa dải trống): cụm tìm + chip co giãn, nút Lọc nâng cao đứng ngay trước nút Cột. Màn hẹp thì cụm tìm + chip
 * xuống dòng trước. "Xóa lọc" nằm cuối cụm, cùng nếp màn Bảng giá VTBB.
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
  /** Có bộ lọc nào đang bật (tìm, chip xu hướng hoặc lọc nâng cao) → hiện "Xóa lọc". */
  filtersActive: boolean
  onReset: () => void
}) {
  return (
    <>
      <div className="pkg-row" style={{ flex: '1 1 320px', minWidth: 0 }}>
        <div className="pkg-search">
          <input aria-label="Tìm sản phẩm" placeholder="Tìm mã HH, tên, mã thành phần…" value={keyword}
            onChange={(e) => onKeyword(e.target.value)} />
        </div>
        <div className="pkg-pills" role="group" aria-label="Lọc theo xu hướng chi phí">
          {OVERVIEW_TREND_CHIPS.map((c) => (
            <button key={c.value} type="button" title={c.title} className={'pkg-pill' + (trend === c.value ? ' on' : '')}
              aria-pressed={trend === c.value} onClick={() => onTrend(c.value)}>{overviewChipLabel(c, counts)}</button>
          ))}
        </div>
        {filtersActive && <button className="btn ghost sm" onClick={onReset}><i className="ti ti-rotate" />Xóa lọc</button>}
      </div>
      <PackagingImpactAdvancedFilter variant="overview" value={advanced} onApply={onAdvanced} />
    </>
  )
}
