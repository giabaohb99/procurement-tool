/**
 * duoc-CR-784 — ô số dùng chung của các bảng Giá bao bì.
 *
 * Chưa có giá thì trả `<span>—</span>` chứ không trả chuỗi `'—'`: `DataTable` cố ý đổi ô chuỗi gạch trần
 * thành ô trống (CR-132), mà ô trống ở cột giá đọc như "giá 0".
 */
import { cn } from '@/shared/utils/cn'

import {
  formatPackagingDiff,
  formatPackagingPercent,
  formatPackagingPrice,
  packagingDiffTone,
} from '../utils/packaging-price-format'

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

/** Hai số "a – b" trong một ô (min–max, sàn–trần); cả hai trống thì gạch. */
export function RangeText({
  low,
  high,
  danger = false,
}: {
  low: Num
  high: Num
  danger?: boolean
}) {
  const a = formatPackagingPrice(low)
  const b = formatPackagingPrice(high)
  if (!a && !b) return <EmptyDash />
  return (
    <span className={cn('tabular-nums', danger && 'font-semibold text-destructive')}>
      {a || '…'} – {b || '…'}
    </span>
  )
}
