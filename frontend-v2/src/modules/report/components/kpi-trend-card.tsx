import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react'
import { Line, LineChart, ResponsiveContainer, YAxis } from 'recharts'

import { Card } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'

interface KpiTrendCardProps {
  label: string
  value: string
  /**
   * Thay đổi so với kỳ trước. `null` = không so được (kỳ trước bằng 0, hoặc
   * hai kỳ không cùng độ dài) — khi đó thẻ hiện `hint` thay cho dải so sánh.
   */
  change?: number | null
  /** Đơn vị của `change`: `%` (tương đối) hay `điểm` (chênh tỷ lệ tuyệt đối). */
  changeUnit?: '%' | 'điểm'
  /** Chữ sau con số thay đổi, vd "so với cùng kỳ 2025". */
  changeCaption?: string
  /**
   * Chiều nào là TỐT. Bỏ trống = trung tính: chi tiêu tăng chưa chắc là xấu,
   * tô xanh/đỏ bừa là gán nghĩa cho con số không có nghĩa đó.
   */
  goodDirection?: 'up' | 'down'
  /** Dòng phụ — hiện khi không có `change`, hoặc kèm thêm dưới dải so sánh. */
  hint?: string
  tone?: 'danger'
  /** Đường xu hướng mini (12 tháng). Bỏ trống = không vẽ. */
  sparkline?: number[]
  loading?: boolean
  /** Lớp phụ cho ô lưới, vd cho thẻ lẻ cuối hàng trải hết bề ngang. */
  className?: string
}

/** Định dạng thay đổi có dấu: +12,3% · −4 điểm. */
function formatChange(change: number, unit: '%' | 'điểm'): string {
  const abs = Math.abs(change).toLocaleString('vi-VN', { maximumFractionDigits: 1 })
  const sign = change > 0 ? '+' : change < 0 ? '−' : ''
  return unit === '%' ? `${sign}${abs}%` : `${sign}${abs} điểm`
}

/**
 * Thẻ KPI kiểu báo cáo Haravan: con số lớn + mũi tên thay đổi so với kỳ trước
 * + đường xu hướng mini ở chân thẻ.
 *
 * Màu của dải thay đổi đi KÈM mũi tên và dấu +/−, không bao giờ mang nghĩa một
 * mình (người mù màu vẫn đọc được chiều tăng giảm).
 */
export function KpiTrendCard({
  label,
  value,
  change,
  changeUnit = '%',
  changeCaption,
  goodDirection,
  hint,
  tone,
  sparkline,
  loading = false,
  className,
}: KpiTrendCardProps) {
  const hasChange = typeof change === 'number' && Number.isFinite(change)
  const rounded = hasChange ? Math.round(change * 10) / 10 : 0
  const direction = rounded > 0 ? 'up' : rounded < 0 ? 'down' : 'flat'
  const toneClass =
    !goodDirection || direction === 'flat'
      ? 'text-muted-foreground'
      : direction === goodDirection
        ? 'text-success'
        : 'text-destructive'
  const Arrow = direction === 'up' ? ArrowUpRight : direction === 'down' ? ArrowDownRight : Minus
  const points = sparkline?.map((v, i) => ({ i, v }))

  return (
    // `min-w-0`: cùng chốt chống tràn ngang của ChartCard — recharts báo ngược
    // bề rộng tối thiểu và nong cả lưới ra trên điện thoại.
    <Card className={cn('min-w-0 gap-2 p-4', className)}>
      <p className="truncate text-sm text-muted-foreground" title={label}>
        {label}
      </p>
      {loading ? (
        <>
          <Skeleton className="h-7 w-2/3" />
          <Skeleton className="h-4 w-1/2" />
        </>
      ) : (
        <>
          <p className="truncate text-2xl font-semibold tabular-nums text-navy dark:text-foreground">
            {value}
          </p>
          {hasChange && (
            <p className="flex items-center gap-1 text-xs">
              <span className={cn('inline-flex items-center gap-0.5 font-medium', toneClass)}>
                <Arrow className="size-3.5" aria-hidden />
                {formatChange(rounded, changeUnit)}
              </span>
              {changeCaption && <span className="truncate text-muted-foreground">{changeCaption}</span>}
            </p>
          )}
          {hint && (
            <p
              className={cn(
                'truncate text-xs text-muted-foreground',
                tone === 'danger' && 'text-destructive',
              )}
              title={hint}
            >
              {hint}
            </p>
          )}
        </>
      )}
      {/* Toàn số 0 thì không vẽ: một đường phẳng ở đáy trông như dữ liệu thật. */}
      {points && points.length > 1 && points.some((p) => p.v !== 0) && !loading && (
        <div className="-mx-1 mt-1 h-10" aria-hidden>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={points} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
              <YAxis hide domain={[0, 'dataMax']} />
              <Line
                type="monotone"
                dataKey="v"
                stroke="var(--chart-1)"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  )
}
