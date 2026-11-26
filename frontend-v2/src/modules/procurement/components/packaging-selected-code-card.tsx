/**
 * duoc-CR-784 — THẺ điện thoại của một MÃ ĐÃ CHỌN ở màn Tác động giá (bảng `PackagingImpactSelectedTable`).
 *
 * Bố cục "lưới 2×2 gọn" (người chủ chốt 26/11/2026): dòng mã · nhóm + nút bỏ; tên tối đa hai dòng; bốn ô đều nhau
 * (Giá cũ · Giá mới · Chênh lệch · Giá giả định); một dòng chân mờ "n SP bị ảnh hưởng · Min–Max a – b" (+ cảnh báo).
 *
 * Ô giá giả định VẪN GÕ ĐƯỢC ngay trên thẻ — đó là việc chính của màn này (mô phỏng trước khi NCC chốt giá). Thẻ không
 * bấm cả khối (bảng không có `onRowClick`), nên mã bấm sang Lịch sử và nút bỏ mã nằm trong thẻ được. "Giá mới" đọc
 * `row.new` y như cột của bảng (giá giả định chỉ làm đổi Chênh lệch / %, không đổi ô này).
 */
import { TriangleAlert, X } from 'lucide-react'

import { Button } from '@/shared/ui/button'

import type { PackagingSelectedCode } from '../types/packaging-cost-types'
import { formatPackagingPrice } from '../utils/packaging-price-format'
import { joinPackagingWarnings } from '../utils/packaging-warning-text'
import { PackagingAssumedPriceInput } from './packaging-assumed-price-input'
import { PackagingCodeLink } from './packaging-code-link'
import { PackagingCardTile } from './packaging-mobile-card-parts'
import { DiffText, PercentText, PriceText } from './packaging-price-cells'

interface PackagingSelectedCodeCardProps {
  row: PackagingSelectedCode
  /** Giá đang gõ (chưa qua trễ) — cùng nguồn với ô của bảng. */
  assumed: number | undefined
  onAssumedChange: (code: string, price: number | null) => void
  onRemove: (code: string) => void
}

export function PackagingSelectedCodeCard({
  row,
  assumed,
  onAssumedChange,
  onRemove,
}: PackagingSelectedCodeCardProps) {
  const warnings = joinPackagingWarnings(row.warnings)
  const range = `${formatPackagingPrice(row.min) || '—'} – ${formatPackagingPrice(row.max) || '—'}`
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div className="flex min-w-0 flex-1 items-baseline gap-2">
          <PackagingCodeLink code={row.code} />
          {row.group && <span className="truncate text-xs text-muted-foreground">· {row.group}</span>}
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="-mr-1.5 size-8 shrink-0"
          aria-label={`Bỏ ${row.code}`}
          onClick={() => onRemove(row.code)}
        >
          <X className="size-4" />
        </Button>
      </div>
      {/*  Tên vật tư dài: tối đa hai dòng rồi "…", đủ chữ ở `title`. */}
      <div className="line-clamp-2 text-sm leading-snug" title={row.name}>
        {row.name || <span className="text-muted-foreground">(chưa có tên)</span>}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <PackagingCardTile label="Giá cũ">
          <PriceText value={row.old} />
        </PackagingCardTile>
        <PackagingCardTile label="Giá mới">
          <PriceText value={row.new} />
        </PackagingCardTile>
        <PackagingCardTile label="Chênh lệch">
          <span className="flex min-w-0 items-baseline gap-1.5 whitespace-nowrap">
            <DiffText value={row.diff} bold />
            <span className="text-xs font-normal">
              <PercentText value={row.pct} />
            </span>
          </span>
        </PackagingCardTile>
        <PackagingCardTile label="Giá giả định">
          <PackagingAssumedPriceInput
            code={row.code}
            value={assumed}
            onChange={onAssumedChange}
            className="h-8 w-full min-w-0 px-2 text-sm font-semibold"
          />
        </PackagingCardTile>
      </div>

      <p className="text-xs text-muted-foreground">
        {row.usage.toLocaleString('vi-VN')} SP bị ảnh hưởng · Min–Max {range}
      </p>

      {warnings && (
        <p className="flex items-start gap-1.5 text-xs text-destructive">
          <TriangleAlert className="mt-px size-3.5 shrink-0" aria-hidden="true" />
          <span>{warnings}</span>
        </p>
      )}
    </div>
  )
}
