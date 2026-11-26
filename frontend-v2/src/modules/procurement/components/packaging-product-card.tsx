/**
 * duoc-CR-784 — THẺ điện thoại của một SẢN PHẨM, dùng chung cho bảng "Sản phẩm bị ảnh hưởng" (Tác động giá) và "Tổng hợp
 * theo sản phẩm" — cùng hình dòng `PackagingImpactProduct`, cùng `buildPackagingProductColumns` ở bảng.
 *
 * Tầng số chính: chi phí bao bì /chai cũ → mới (mới là giá đang áp ở Tác động, giá mới ở Tổng hợp), rồi tăng / giảm
 * /chai và /thùng tô xanh / đỏ đúng như ô bảng. Năm thành phần thành năm dòng gọn "mã · cũ → mới"; mã đang chọn tô nền.
 * Bản `overview` thêm "% chênh" và huy hiệu xu hướng, mã HH + mã thành phần bấm được sang Lịch sử (như bảng `compact`).
 */
import { TriangleAlert } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'

import { PACKAGING_PART_COLUMNS, packagingPartHeader } from '../config/packaging-part-columns'
import type { PackagingImpactProduct } from '../types/packaging-cost-types'
import { joinPackagingWarnings } from '../utils/packaging-warning-text'
import { PackagingCodeLink } from './packaging-code-link'
import {
  PackagingCardPartLine,
  PackagingCardStats,
  PackagingCardTitle,
} from './packaging-mobile-card-parts'
import { DiffText, PercentText, PriceChangeText, TrendText } from './packaging-price-cells'

interface PackagingProductCardProps {
  row: PackagingImpactProduct
  /** `impact` = Tác động giá (mới = giá đang áp); `overview` = Tổng hợp theo sản phẩm (mới = giá mới, có % chênh + xu hướng). */
  variant: 'impact' | 'overview'
}

export function PackagingProductCard({ row, variant }: PackagingProductCardProps) {
  const overview = variant === 'overview'
  const newCost = overview ? row.cost_new_bottle : row.cost_applied_bottle
  const warnings = joinPackagingWarnings(row.warnings)
  return (
    <div className="space-y-2.5">
      <PackagingCardTitle
        code={overview ? <PackagingCodeLink code={row.fg_code} product /> : row.fg_code}
        name={row.fg_name}
        aside={
          overview && (
            <Badge variant="outline">
              <TrendText trend={row.trend} />
            </Badge>
          )
        }
      />

      <PackagingCardStats
        items={[
          {
            //  "% chênh" của Tổng hợp đi kèm chính con số chi phí (cột riêng ở bảng): ba ô một hàng ở 390px thì nhãn
            //  "Tăng/giảm /chai" bị cắt còn "Tăng/giảm /c…".
            label: overview ? 'CP cũ → mới /chai · % chênh' : 'CP bao bì/chai cũ → mới',
            value: (
              <span className="flex items-baseline gap-1.5">
                <PriceChangeText from={row.cost_old_bottle} to={newCost} />
                {overview && (
                  <span className="text-xs font-normal">
                    <PercentText value={row.pct} />
                  </span>
                )}
              </span>
            ),
            wide: true,
          },
          { label: 'Tăng/giảm /chai', value: <DiffText value={row.diff_bottle} bold /> },
          { label: 'Tăng/giảm /thùng', value: <DiffText value={row.diff_carton} bold /> },
        ]}
      />

      <ul className="space-y-1">
        {/*  Quy cách thùng đứng đầu danh sách thành phần: nó là mẫu số của hai dòng "(giá /thùng)" bên dưới. */}
        <PackagingCardPartLine
          label={overview ? 'Quy cách' : 'Quy cách thùng'}
          code={row.carton_qty ? row.carton_qty.toLocaleString('vi-VN') : '—'}
        />
        {PACKAGING_PART_COLUMNS.map((column) => {
          const part = row.parts.find((item) => item.role === column.role)
          const label = packagingPartHeader(column)
          if (!part?.code) return <PackagingCardPartLine key={column.role} label={label} code="—" />
          return (
            <PackagingCardPartLine
              key={column.role}
              label={label}
              highlight={part.selected}
              code={overview ? <PackagingCodeLink code={part.code} /> : part.code}
              detail={<PriceChangeText from={part.old} to={part.applied ?? part.new} />}
            />
          )
        })}
      </ul>

      {warnings && (
        <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
          <TriangleAlert className="mt-px size-3.5 shrink-0 text-amber-600" aria-hidden="true" />
          <span>{warnings}</span>
        </p>
      )}
    </div>
  )
}
