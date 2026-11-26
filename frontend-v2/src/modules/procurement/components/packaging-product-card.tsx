/**
 * duoc-CR-784 — THẺ điện thoại của một SẢN PHẨM, dùng chung cho bảng "Sản phẩm bị ảnh hưởng" (Tác động giá) và "Tổng hợp
 * theo sản phẩm" — cùng hình dòng `PackagingImpactProduct`, cùng `buildPackagingProductColumns` ở bảng.
 *
 * Bố cục "lưới 2×2 gọn" (người chủ chốt 26/11/2026, cùng kiểu thẻ Mã đã chọn): dòng mã (+ huy hiệu xu hướng ở Tổng hợp),
 * tên mờ tối đa hai dòng, bốn ô đều nhau (CP cũ /chai · CP mới /chai · Tăng/giảm /chai · Tăng/giảm /thùng; mới là giá đang áp ở
 * Tác động, giá mới ở Tổng hợp), rồi các thành phần thành lưới ba cột vai trò | mã | cũ → mới. Thành phần chưa khai mã thì
 * ẩn dòng (thiếu mã đã có dòng cảnh báo hổ phách bên dưới). Mã đang chọn tô nền vàng. Bản `overview` thêm "% chênh" dưới
 * tăng/giảm /chai, mã HH + mã thành phần bấm được sang Lịch sử (như bảng `compact`).
 */
import { TriangleAlert } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'

import { PACKAGING_PART_COLUMNS } from '../config/packaging-part-columns'
import type { PackagingImpactProduct } from '../types/packaging-cost-types'
import { joinPackagingWarnings, packagingRoleLabel } from '../utils/packaging-warning-text'
import { PackagingCodeLink } from './packaging-code-link'
import { PackagingCardTile } from './packaging-mobile-card-parts'
import { DiffText, PercentText, PriceChangeText, PriceText, TrendText } from './packaging-price-cells'

interface PackagingProductCardProps {
  row: PackagingImpactProduct
  /** `impact` = Tác động giá (mới = giá đang áp); `overview` = Tổng hợp theo sản phẩm (mới = giá mới, có % chênh + xu hướng). */
  variant: 'impact' | 'overview'
}

export function PackagingProductCard({ row, variant }: PackagingProductCardProps) {
  const overview = variant === 'overview'
  const newCost = overview ? row.cost_new_bottle : row.cost_applied_bottle
  const warnings = joinPackagingWarnings(row.warnings)
  const shownParts = PACKAGING_PART_COLUMNS.flatMap((column) => {
    const part = row.parts.find((item) => item.role === column.role)
    return part?.code ? [{ column, part }] : []
  })
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0 truncate font-semibold tabular-nums">
          {overview ? <PackagingCodeLink code={row.fg_code} product /> : row.fg_code}
        </div>
        {overview && (
          <Badge variant="outline" className="shrink-0">
            <TrendText trend={row.trend} />
          </Badge>
        )}
      </div>
      {/*  Tên hàng hóa dài: tối đa hai dòng rồi "…", đủ chữ ở `title`. */}
      <div className="line-clamp-2 text-sm leading-snug text-muted-foreground" title={row.fg_name}>
        {row.fg_name || '(chưa có tên)'}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <PackagingCardTile label="CP cũ /chai">
          <PriceText value={row.cost_old_bottle} />
        </PackagingCardTile>
        <PackagingCardTile label="CP mới /chai">
          <PriceText value={newCost} />
        </PackagingCardTile>
        <PackagingCardTile label="Tăng/giảm /chai">
          <span className="flex min-w-0 flex-col">
            <DiffText value={row.diff_bottle} bold />
            {overview && (
              <span className="text-xs font-normal leading-tight">
                <PercentText value={row.pct} />
              </span>
            )}
          </span>
        </PackagingCardTile>
        <PackagingCardTile label="Tăng/giảm /thùng">
          <DiffText value={row.diff_carton} bold />
        </PackagingCardTile>
      </div>

      {(shownParts.length > 0 || row.carton_qty > 0) && (
        <div className="space-y-1">
          <div className="flex items-baseline justify-between text-xs text-muted-foreground">
            <span>Thành phần</span>
            {row.carton_qty > 0 && <span>Quy cách {row.carton_qty.toLocaleString('vi-VN')}</span>}
          </div>
          {/*  Lưới chung ba cột (vai trò · mã · giá) để các hàng thẳng cột; mỗi hàng là lưới con nên tô nền được cả hàng. */}
          <ul className="grid grid-cols-[auto_auto_1fr] gap-x-3 text-xs">
            {shownParts.map(({ column, part }) => (
              <li
                key={column.role}
                className={cn(
                  'col-span-3 grid grid-cols-subgrid items-baseline rounded px-1.5 py-0.5',
                  part.selected && 'bg-amber-100 dark:bg-amber-900',
                )}
              >
                <span className="text-muted-foreground">{packagingRoleLabel(column.role)}</span>
                <span className="font-medium tabular-nums">
                  {overview ? <PackagingCodeLink code={part.code} /> : part.code}
                </span>
                <span className="text-right whitespace-nowrap">
                  <PriceChangeText from={part.old} to={part.applied ?? part.new} />
                  {column.perCarton && (part.applied ?? part.new) != null && (
                    <span className="ml-0.5 text-muted-foreground">/thùng</span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {warnings && (
        <p className="flex items-start gap-1.5 text-xs text-amber-700 dark:text-amber-400">
          <TriangleAlert className="mt-px size-3.5 shrink-0" aria-hidden="true" />
          <span>{warnings}</span>
        </p>
      )}
    </div>
  )
}
