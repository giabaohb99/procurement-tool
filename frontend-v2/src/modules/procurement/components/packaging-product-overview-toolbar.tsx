/**
 * duoc-CR-784 — thanh lọc của tab Tổng hợp theo sản phẩm: ô tìm + chip xu hướng KÈM SỐ ĐẾM (người chủ chốt không thích
 * thẻ KPI to, số đếm nằm ngay trên chip). Số đếm là của tập đã lọc theo từ khóa nhưng chưa lọc xu hướng nên chip nào cũng
 * hiện đủ số; bấm chip đang chọn lần nữa không bỏ chọn (muốn bỏ thì bấm "Tất cả").
 */
import { Search } from 'lucide-react'

import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'

import type { PackagingOverviewCounts, PackagingOverviewTrend } from '../types/packaging-cost-types'
import { OVERVIEW_TREND_CHIPS, overviewChipLabel } from '../utils/packaging-product-overview'

interface PackagingProductOverviewToolbarProps {
  keyword: string
  onKeywordChange: (value: string) => void
  trend: PackagingOverviewTrend
  onTrendChange: (value: PackagingOverviewTrend) => void
  counts: PackagingOverviewCounts | undefined
}

export function PackagingProductOverviewToolbar({
  keyword,
  onKeywordChange,
  trend,
  onTrendChange,
  counts,
}: PackagingProductOverviewToolbarProps) {
  return (
    <div className="flex w-full flex-wrap items-center gap-2">
      <div className="relative w-full max-w-xs">
        <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          aria-label="Tìm sản phẩm"
          placeholder="Tìm mã HH, tên, mã thành phần…"
          value={keyword}
          onChange={(event) => onKeywordChange(event.target.value)}
        />
      </div>
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
    </div>
  )
}
