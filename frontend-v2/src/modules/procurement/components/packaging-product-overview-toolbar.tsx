/**
 * duoc-CR-784 — thanh lọc của tab Tổng hợp theo sản phẩm: ô tìm + chip xu hướng KÈM SỐ ĐẾM (người chủ chốt không thích
 * thẻ KPI to, số đếm nằm ngay trên chip) + nút Lọc nâng cao. Số đếm là của tập đã lọc theo từ khóa và lọc nâng cao nhưng
 * chưa lọc xu hướng nên chip nào cũng hiện đủ số; bấm chip đang chọn lần nữa không bỏ chọn (muốn bỏ thì bấm "Tất cả").
 *
 * Bố cục MỘT HÀNG cùng nút Xóa lọc / Tải lại / Cột của bảng (người chủ báo 25/11/2026: hàng thứ hai chỉ có hai nút lệch
 * phải, chừa dải trống): cụm tìm + chip co giãn (`flex-1`), nút Lọc nâng cao bám phía phải của cụm, ngay trước nhóm nút
 * của bảng. Màn hẹp thì cụm tìm + chip xuống dòng trước, nút Lọc nâng cao dồn theo.
 */
import { Search } from 'lucide-react'

import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'

import type { PackagingOverviewCounts, PackagingOverviewTrend } from '../types/packaging-cost-types'
import type { ImpactAdvancedFilters } from '../utils/packaging-impact-filters'
import { OVERVIEW_TREND_CHIPS, overviewChipLabel } from '../utils/packaging-product-overview'
import { PackagingImpactAdvancedFilter } from './packaging-impact-advanced-filter'

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
    <>
      {/*  `flex-[1_1_24rem]` (không `w-full`): cụm này chiếm phần còn lại của hàng để Lọc nâng cao + Tải lại / Cột đứng CÙNG
           hàng bên phải; chỗ trống dưới 24rem thì cả cụm xuống dòng thay vì bóp ô tìm. */}
      <div className="flex min-w-0 flex-[1_1_24rem] flex-wrap items-center gap-2">
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
      <PackagingImpactAdvancedFilter
        variant="overview"
        value={advanced}
        onApply={onAdvancedChange}
      />
    </>
  )
}
