import type { PackagingOverviewCounts, PackagingOverviewTrend } from '../../api/packaging-cost-types'
import { OVERVIEW_TREND_CHIPS, overviewChipLabel } from '../../utils/packaging-overview'
import './packaging.css'

/**
 * Thanh lọc của màn Tổng hợp theo sản phẩm: ô tìm + chip xu hướng KÈM SỐ ĐẾM (người chủ chốt không thích thẻ KPI to).
 * Số đếm là của tập đã lọc theo từ khóa nhưng chưa lọc xu hướng nên chip nào cũng hiện đủ số.
 */
export default function PackagingOverviewToolbar({ keyword, onKeyword, trend, onTrend, counts }: {
  keyword: string
  onKeyword: (v: string) => void
  trend: PackagingOverviewTrend
  onTrend: (v: PackagingOverviewTrend) => void
  counts: PackagingOverviewCounts | undefined
}) {
  return (
    <div className="pkg-row" style={{ padding: '14px 0 10px' }}>
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
    </div>
  )
}
