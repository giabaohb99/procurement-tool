/**
 * duoc-CR-784 — thanh lọc của tab Tổng hợp theo sản phẩm: ô tìm + nút "Thêm điều kiện" + chip điều kiện (thanh lọc chung
 * `PackagingFilterChipBar`) và chip xu hướng KÈM SỐ ĐẾM (người chủ chốt không thích thẻ KPI to, số đếm nằm ngay trên chip).
 * Xu hướng giữ chip đếm riêng nên menu "Thêm điều kiện" của màn này không có mục Xu hướng. Số đếm là của tập đã lọc theo từ
 * khóa và điều kiện nhưng chưa lọc xu hướng nên chip nào cũng hiện đủ số; bấm chip đang chọn lần nữa không bỏ chọn (muốn bỏ
 * thì bấm "Tất cả").
 *
 * Bố cục: hàng một cùng nút Tải lại / Cột của bảng (màn truyền `toolbarActionsClassName="order-2"`), chip điều kiện ở hàng dưới.
 */
import { cn } from '@/shared/utils/cn'

import type { PackagingOverviewCounts, PackagingOverviewTrend } from '../types/packaging-cost-types'
import type { ImpactAdvancedFilters } from '../utils/packaging-impact-filters'
import { OVERVIEW_TREND_CHIPS, overviewChipLabel } from '../utils/packaging-product-overview'
import { PackagingFilterChipBar } from './packaging-filter-chip-bar'

interface PackagingProductOverviewToolbarProps {
  keyword: string
  onKeywordChange: (value: string) => void
  trend: PackagingOverviewTrend
  onTrendChange: (value: PackagingOverviewTrend) => void
  counts: PackagingOverviewCounts | undefined
  /** Bộ lọc nâng cao đang áp. */
  advanced: ImpactAdvancedFilters
  onAdvancedChange: (value: ImpactAdvancedFilters) => void
}

export function PackagingProductOverviewToolbar({
  keyword,
  onKeywordChange,
  trend,
  onTrendChange,
  counts,
  advanced,
  onAdvancedChange,
}: PackagingProductOverviewToolbarProps) {
  return (
    <PackagingFilterChipBar
      variant="overview"
      value={advanced}
      onChange={onAdvancedChange}
      keyword={keyword}
      onKeywordChange={onKeywordChange}
    >
      <div className="flex flex-wrap gap-1" role="group" aria-label="Lọc theo xu hướng chi phí">
        {OVERVIEW_TREND_CHIPS.map((chip) => (
          <button
            key={chip.value}
            type="button"
            title={chip.title}
            aria-pressed={trend === chip.value}
            onClick={() => onTrendChange(chip.value)}
            className={cn(
              'h-8 rounded-full border px-3 text-sm hover:bg-accent',
              trend === chip.value &&
                'border-primary bg-primary text-primary-foreground hover:bg-primary/90',
            )}
          >
            {overviewChipLabel(chip, counts)}
          </button>
        ))}
      </div>
    </PackagingFilterChipBar>
  )
}
