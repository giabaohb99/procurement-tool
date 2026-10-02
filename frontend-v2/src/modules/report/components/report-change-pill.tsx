import { Minus, TrendingDown, TrendingUp } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

import type { MetricChangeDescription } from '../utils/report-period-comparison'

const TONE_CLASS: Record<MetricChangeDescription['tone'], string> = {
  good: 'bg-success/10 text-success',
  bad: 'bg-destructive/10 text-destructive',
  neutral: 'bg-muted text-muted-foreground',
}

/** Bản `inline` (ô bảng): cùng màu chữ, KHÔNG nền — đặt sát con số mà không thành một khối. */
const INLINE_TONE_CLASS: Record<MetricChangeDescription['tone'], string> = {
  good: 'text-success',
  bad: 'text-destructive',
  neutral: 'text-muted-foreground',
}

interface ReportChangePillProps {
  description: MetricChangeDescription
  /** `pill` (mặc định, thẻ KPI) có nền bo tròn; `inline` (dòng Tổng của bảng) chỉ là chữ màu. */
  variant?: 'pill' | 'inline'
  className?: string
}

/**
 * "Pill" thay đổi so với kỳ trước — nguồn hiển thị DUY NHẤT dùng chung cho thẻ
 * KPI (`KpiTrendCard`) VÀ dòng Tổng của bảng "Xem theo" (`ReportGroupedTable`),
 * để hai nơi đó luôn đọc cùng một quy ước icon/màu thay vì mỗi nơi tự vẽ một
 * kiểu mũi tên riêng (đúng thứ đã gây rối mắt ở bản UI cũ — không còn glyph chữ
 * "↘/↗" nào trong toàn phân hệ).
 *
 * `kind: 'unavailable'` KHÔNG vẽ gì (chưa có dữ liệu để so, hoặc đang tắt so
 * sánh) — trả `null` để chỗ gọi khỏi phải tự kiểm tra trước khi render.
 */
export function ReportChangePill({
  description,
  variant = 'pill',
  className,
}: ReportChangePillProps) {
  if (description.kind === 'unavailable') return null

  const Icon =
    description.direction === 'up'
      ? TrendingUp
      : description.direction === 'down'
        ? TrendingDown
        : Minus

  return (
    <span
      className={cn(
        'inline-flex w-fit shrink-0 items-center gap-1 text-xs font-medium whitespace-nowrap',
        variant === 'pill'
          ? cn('rounded-full px-1.5 py-0.5', TONE_CLASS[description.tone])
          : INLINE_TONE_CLASS[description.tone],
        className,
      )}
    >
      {/*  "Mới" không phải một CHIỀU tăng/giảm — không có mũi tên nào đúng nghĩa
           cho nó, nên bỏ icon thay vì gắn bừa một chiều không thật. */}
      {description.kind !== 'new' && <Icon className="size-3" aria-hidden />}
      {description.text}
    </span>
  )
}
