import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './card'
import { Skeleton } from './skeleton'

/** Một hạng mục trên biểu đồ: nhãn hiển thị + số đo. */
export interface ChartDatum {
  label: string
  value: number
}

/**
 * Bảng màu biểu đồ. Gán theo THỨ TỰ CỐ ĐỊNH cho từng thực thể (trạng thái, loại…),
 * KHÔNG gán theo thứ hạng: lọc bớt dữ liệu mà màu các phần còn lại đổi theo thì
 * người đọc đã quen "Chính thức màu xanh" sẽ hiểu sai. Giá trị thật khai trong
 * `index.css` (mỗi tông có bậc riêng cho nền sáng và nền tối).
 */
export const CHART_COLORS = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
] as const

/** Xám trung tính cho nhóm gom "Khác" — không nằm trong dải phân loại. */
export const CHART_NEUTRAL = 'var(--chart-neutral)'

interface ChartCardProps {
  title: string
  /** Câu mô tả ngắn dưới tiêu đề — nói rõ biểu đồ đếm cái gì. */
  description?: string
  loading?: boolean
  /** Đã tải xong nhưng không có dữ liệu để vẽ. */
  isEmpty?: boolean
  emptyLabel?: string
  className?: string
  children: ReactNode
}

/**
 * Khung chung của một thẻ biểu đồ (tiêu đề + trạng thái tải/rỗng) để các phân hệ
 * không mỗi nơi dựng một kiểu.
 */
export function ChartCard({
  title,
  description,
  loading = false,
  isEmpty = false,
  emptyLabel = 'Chưa có dữ liệu để hiển thị.',
  className,
  children,
}: ChartCardProps) {
  return (
    // `h-full` + nội dung căn giữa dọc: thẻ cùng hàng luôn cao bằng nhau, biểu
    // đồ ít dòng thì nằm giữa thẻ chứ không dồn lên đầu bỏ trống một mảng dưới.
    <Card className={cn('h-full gap-4', className)}>
      <CardHeader className="pb-0">
        {/* `dark:text-foreground` vì --navy là màu thương hiệu cố định, để
            nguyên trên nền tối sẽ chìm hẳn. */}
        <CardTitle className="text-base text-navy dark:text-foreground">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>

      <CardContent className="flex flex-1 flex-col">
        {loading ? (
          <div className="space-y-3 py-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/3" />
          </div>
        ) : isEmpty ? (
          <p className="py-8 text-center text-sm text-muted-foreground">{emptyLabel}</p>
        ) : (
          children
        )}
      </CardContent>
    </Card>
  )
}

/** Một dòng trong chú giải: chấm màu + nhãn + số liệu. */
export function ChartLegendItem({
  color,
  label,
  value,
  hint,
}: {
  color: string
  label: string
  value: string
  /** Chữ phụ bên phải, vd tỉ lệ phần trăm. */
  hint?: string
}) {
  return (
    <li className="flex items-center gap-2 text-sm">
      {/* Chấm màu đứng CẠNH chữ — chữ luôn dùng token text, không tô màu chuỗi
          dữ liệu (tông nhạt như vàng/xanh ngọc đọc không nổi trên nền trắng). */}
      <span
        aria-hidden
        className="size-2.5 shrink-0 rounded-full"
        style={{ backgroundColor: color }}
      />
      <span className="min-w-0 flex-1 truncate text-muted-foreground" title={label}>
        {label}
      </span>
      <span className="shrink-0 font-medium tabular-nums text-foreground">{value}</span>
      {hint && <span className="w-12 shrink-0 text-right tabular-nums text-muted-foreground">{hint}</span>}
    </li>
  )
}

/** Một mục trong `payload` mà recharts truyền vào tooltip. */
interface TooltipPayloadItem {
  name?: string | number
  value?: number | string
  color?: string
  payload?: Record<string, unknown>
}

interface ChartTooltipContentProps {
  active?: boolean
  payload?: TooltipPayloadItem[]
  label?: string | number
  /** Định dạng số hiển thị; mặc định là số nguyên theo locale vi-VN. */
  formatValue?: (value: number) => string
  /** Đơn vị đặt sau số, vd "nhân sự". */
  unit?: string
}

/**
 * Nội dung tooltip dùng chung. SỐ đứng trước và đậm, tên hạng mục là chữ phụ —
 * người đọc đã biết mình trỏ vào đâu, thứ họ cần là con số.
 *
 * Tooltip chỉ để xem nhanh: mọi giá trị đều đã được ghi thẳng trên biểu đồ hoặc
 * trong chú giải, không có số nào chỉ hiện khi rê chuột.
 */
export function ChartTooltipContent({
  active,
  payload,
  label,
  formatValue = (value) => value.toLocaleString('vi-VN'),
  unit,
}: ChartTooltipContentProps) {
  if (!active || !payload?.length) return null

  const item = payload[0]
  const raw = typeof item.value === 'number' ? item.value : Number(item.value ?? 0)
  const title = String(label ?? item.name ?? '')

  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-popover-foreground shadow-md">
      <p className="text-sm font-semibold tabular-nums">
        {formatValue(raw)}
        {unit ? ` ${unit}` : ''}
      </p>
      <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
        {item.color && (
          <span
            aria-hidden
            className="h-0.5 w-3 shrink-0 rounded-full"
            style={{ backgroundColor: item.color }}
          />
        )}
        {title}
      </p>
    </div>
  )
}
