/**
 * duoc-CR-784 — ô số dùng chung của các bảng Giá bao bì.
 *
 * Chưa có giá thì trả `<span>—</span>` chứ không trả chuỗi `'—'`: `DataTable` cố ý đổi ô chuỗi gạch trần
 * thành ô trống (CR-132), mà ô trống ở cột giá đọc như "giá 0".
 */
import { PACKAGING_COST_TREND_CODE } from '@/shared/constants/statuses'
import { cn } from '@/shared/utils/cn'

import {
  formatPackagingDiff,
  formatPackagingPercent,
  formatPackagingPrice,
  packagingDiffTone,
} from '../utils/packaging-price-format'
import { costTrendLabel } from '../utils/packaging-warning-text'

type Num = number | null | undefined

export function EmptyDash() {
  return <span className="text-muted-foreground">—</span>
}

export function PriceText({ value, className }: { value: Num; className?: string }) {
  const text = formatPackagingPrice(value)
  return text ? <span className={cn('tabular-nums', className)}>{text}</span> : <EmptyDash />
}

export function DiffText({ value, bold = false }: { value: Num; bold?: boolean }) {
  const text = formatPackagingDiff(value)
  if (!text) return <EmptyDash />
  return (
    <span className={cn('tabular-nums', bold && 'font-semibold', packagingDiffTone(value))}>
      {text}
    </span>
  )
}

export function PercentText({ value }: { value: Num }) {
  const text = formatPackagingPercent(value)
  if (!text) return <EmptyDash />
  return <span className={cn('tabular-nums', packagingDiffTone(value))}>{text}</span>
}

/**
 * Giá "cũ → mới" gọn trong một dòng: đổi giá thì số cũ mờ + mũi tên + số mới đậm tô theo chiều (tăng xanh, giảm đỏ); không
 * đổi thì một số; chưa có giá mới thì nói thẳng "chưa có giá". Dùng ở ô thành phần của bảng sản phẩm và ở thẻ điện thoại.
 */
export function PriceChangeText({ from, to }: { from: Num; to: Num }) {
  if (to == null) return <span className="text-muted-foreground">chưa có giá</span>
  const changed = from != null && Math.abs(to - from) > 1e-9
  if (!changed) return <span className="tabular-nums">{formatPackagingPrice(to)}</span>
  return (
    <span className="tabular-nums">
      <span className="text-muted-foreground">{formatPackagingPrice(from)} →</span>{' '}
      <span className={cn('font-semibold', packagingDiffTone(to - (from ?? 0)))}>
        {formatPackagingPrice(to)}
      </span>
    </span>
  )
}

/**
 * Xu hướng chi phí của một sản phẩm (mã `CostTrend`): chữ + màu theo chiều (tăng xanh, giảm đỏ — cùng luật với ô chênh lệch);
 * không đổi / chưa có giá để màu mờ. Tăng kèm gợi ý "cần xem lại giá bán" ở chú giải.
 */
export function TrendText({ trend }: { trend: number }) {
  const tone =
    trend === PACKAGING_COST_TREND_CODE.UP
      ? packagingDiffTone(1)
      : trend === PACKAGING_COST_TREND_CODE.DOWN
        ? packagingDiffTone(-1)
        : 'text-muted-foreground'
  return (
    <span
      className={cn('font-medium', tone)}
      title={trend === PACKAGING_COST_TREND_CODE.UP ? 'Chi phí tăng — cần xem lại giá bán' : undefined}
    >
      {costTrendLabel(trend)}
    </span>
  )
}
