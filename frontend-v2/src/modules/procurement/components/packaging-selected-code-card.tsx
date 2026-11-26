/**
 * duoc-CR-784 — THẺ điện thoại của một MÃ ĐÃ CHỌN ở màn Tác động giá (bảng `PackagingImpactSelectedTable`).
 *
 * Ô giá giả định VẪN GÕ ĐƯỢC ngay trên thẻ — đó là việc chính của màn này (mô phỏng trước khi NCC chốt giá). Thẻ không
 * bấm cả khối (bảng không có `onRowClick`), nên mã bấm sang Lịch sử và nút bỏ mã nằm trong thẻ được.
 */
import { TriangleAlert, X } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'

import type { PackagingSelectedCode } from '../types/packaging-cost-types'
import { joinPackagingWarnings } from '../utils/packaging-warning-text'
import { PackagingAssumedPriceInput } from './packaging-assumed-price-input'
import { PackagingCodeLink } from './packaging-code-link'
import {
  PackagingCardFields,
  PackagingCardStats,
  PackagingCardTitle,
} from './packaging-mobile-card-parts'
import { DiffText, PercentText, PriceChangeText, PriceText } from './packaging-price-cells'

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
  return (
    <div className="space-y-2.5">
      <PackagingCardTitle
        code={<PackagingCodeLink code={row.code} />}
        name={row.name}
        aside={
          <div className="flex items-center gap-1">
            {row.group && <Badge variant="secondary">{row.group}</Badge>}
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-8"
              aria-label={`Bỏ ${row.code}`}
              onClick={() => onRemove(row.code)}
            >
              <X className="size-4" />
            </Button>
          </div>
        }
      />

      <PackagingCardStats
        items={[
          { label: 'Giá cũ → Giá mới', value: <PriceChangeText from={row.old} to={row.new} /> },
          {
            label: 'Chênh lệch',
            value: (
              <span className="flex items-baseline gap-1.5">
                <DiffText value={row.diff} bold />
                <span className="text-xs font-normal">
                  <PercentText value={row.pct} />
                </span>
              </span>
            ),
          },
        ]}
      />

      <label className="flex items-center gap-2 text-sm">
        <span className="shrink-0 text-muted-foreground">Giá giả định</span>
        <PackagingAssumedPriceInput
          code={row.code}
          value={assumed}
          onChange={onAssumedChange}
          className="h-9 flex-1"
        />
      </label>

      <PackagingCardFields
        columns={3}
        items={[
          { label: 'Số SP bị ảnh hưởng', value: row.usage.toLocaleString('vi-VN') },
          { label: 'Min', value: <PriceText value={row.min} /> },
          { label: 'Max', value: <PriceText value={row.max} /> },
        ]}
      />

      {warnings && (
        <p className="flex items-start gap-1.5 text-xs text-destructive">
          <TriangleAlert className="mt-px size-3.5 shrink-0" aria-hidden="true" />
          <span>{warnings}</span>
        </p>
      )}
    </div>
  )
}
