/**
 * duoc-CR-784 — THẺ điện thoại của một dòng BẢNG GIÁ VTBB (`usePackagingPriceListColumns`).
 *
 * Số chính: giá cũ → giá mới, chênh lệch kèm %. Trường phụ theo đúng tên cột: số lần mua, mua gần nhất, giá mua gần nhất /
 * lần trước, báo giá mới (giá + ngày hiệu lực), số SP đang dùng, min, max. Nút "Báo giá" của cột Thao tác nằm cuối thẻ
 * (thẻ không bấm cả khối nên đặt nút được).
 */
import { TriangleAlert } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { formatDate } from '@/shared/utils/format-date'

import type { PackagingPriceRow } from '../types/packaging-cost-types'
import { joinPackagingWarnings } from '../utils/packaging-warning-text'
import { PackagingCodeLink } from './packaging-code-link'
import {
  PackagingCardFields,
  PackagingCardStats,
  PackagingCardTitle,
} from './packaging-mobile-card-parts'
import { DiffText, EmptyDash, PercentText, PriceChangeText, PriceText } from './packaging-price-cells'

interface PackagingPriceRowCardProps {
  row: PackagingPriceRow
  /** Có quyền tạo báo giá → hiện nút "Báo giá" (mở hộp Báo giá mới điền sẵn mã). */
  onQuote?: (row: PackagingPriceRow) => void
  /** Dòng của Bảng giá nguyên liệu (bao-CR-800): mã chữ thường, không có Số SP đang dùng — khớp bộ cột của màn đó. */
  rawMaterial?: boolean
}

export function PackagingPriceRowCard({ row, onQuote, rawMaterial = false }: PackagingPriceRowCardProps) {
  const warnings = joinPackagingWarnings(row.warnings)
  return (
    <div className="space-y-2.5">
      <PackagingCardTitle
        code={rawMaterial ? row.code : <PackagingCodeLink code={row.code} />}
        name={row.name}
        aside={
          <>
            {row.group && <Badge variant="secondary">{row.group}</Badge>}
            {row.unit && <span className="text-xs text-muted-foreground">{row.unit}</span>}
          </>
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

      <PackagingCardFields
        items={[
          { label: 'Số lần mua', value: row.purchase_count.toLocaleString('vi-VN') },
          {
            label: 'Mua gần nhất',
            value: row.last_date ? formatDate(row.last_date) : <EmptyDash />,
          },
          { label: 'Giá mua gần nhất', value: <PriceText value={row.last_purchase_price} /> },
          { label: 'Giá mua lần trước', value: <PriceText value={row.prev_purchase_price} /> },
          {
            label: 'Báo giá mới',
            value: row.quote ? (
              <>
                <PriceText value={row.quote.price} />{' '}
                <span className="text-xs text-muted-foreground">
                  {formatDate(row.quote.valid_from)}
                </span>
              </>
            ) : (
              <EmptyDash />
            ),
          },
          ...(rawMaterial ? [] : [{ label: 'Số SP đang dùng', value: row.usage.toLocaleString('vi-VN') }]),
          { label: 'Min', value: <PriceText value={row.min} /> },
          { label: 'Max', value: <PriceText value={row.max} /> },
          { label: 'Tiền tệ', value: 'VND' },
        ]}
      />

      {warnings && (
        <p className="flex items-start gap-1.5 text-xs text-destructive">
          <TriangleAlert className="mt-px size-3.5 shrink-0" aria-hidden="true" />
          <span>{warnings}</span>
        </p>
      )}

      {onQuote && (
        <Button type="button" size="sm" variant="outline" className="w-full" onClick={() => onQuote(row)}>
          Báo giá
        </Button>
      )}
    </div>
  )
}
