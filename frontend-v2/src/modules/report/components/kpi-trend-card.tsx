import { Line, LineChart, ResponsiveContainer, YAxis } from 'recharts'

import { Card } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'

import type { MetricChangeDescription } from '../utils/report-period-comparison'
import { ReportChangePill } from './report-change-pill'

interface KpiTrendCardProps {
  label: string
  value: string
  /**
   * Thay đổi so với kỳ trước, đã phân loại sẵn (`describeMetricChange`).
   * Bỏ trống/`kind: 'unavailable'` = không so được — thẻ hiện `hint` thay cho
   * dải "pill".
   */
  changeDescription?: MetricChangeDescription
  /** Chữ sau "pill" thay đổi, vd "so với cùng kỳ 2025". */
  changeCaption?: string
  /** Dòng phụ — hiện khi không có "pill" để hiện, hoặc kèm thêm dưới dải so sánh. */
  hint?: string
  tone?: 'danger'
  /** Đường xu hướng mini (12 tháng). Bỏ trống = không vẽ. */
  sparkline?: number[]
  loading?: boolean
  /** Lớp phụ cho ô lưới, vd cho thẻ lẻ cuối hàng trải hết bề ngang. */
  className?: string
  /**
   * Bấm được để CHỌN — dùng ở trang báo cáo Haravan (`ReportKpiRow`): bấm một
   * thẻ KPI đổi chỉ số đang vẽ trên biểu đồ xu hướng. Bỏ trống = thẻ tĩnh, giữ
   * đúng hành vi cũ của các trang biểu đồ Thu mua hiện có.
   */
  onClick?: () => void
  /** Đang là chỉ số được chọn — viền nổi bật. Chỉ có nghĩa cùng `onClick`. */
  selected?: boolean
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
  changeDescription,
  changeCaption,
  hint,
  tone,
  sparkline,
  loading = false,
  className,
  onClick,
  selected = false,
}: KpiTrendCardProps) {
  const hasChange = changeDescription && changeDescription.kind !== 'unavailable'
  const points = sparkline?.map((v, i) => ({ i, v }))

  return (
    // `min-w-0`: cùng chốt chống tràn ngang của ChartCard — recharts báo ngược
    // bề rộng tối thiểu và nong cả lưới ra trên điện thoại.
    <Card
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={
        onClick
          ? (event) => {
              if (event.key !== 'Enter' && event.key !== ' ') return
              event.preventDefault()
              onClick()
            }
          : undefined
      }
      className={cn(
        'min-w-0 gap-2 p-4',
        onClick && 'cursor-pointer transition-colors hover:bg-row-hover',
        selected && 'ring-2 ring-primary',
        className,
      )}
    >
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
          <p className="truncate text-2xl font-semibold text-navy tabular-nums dark:text-foreground">
            {value}
          </p>
          {hasChange && changeDescription && (
            <p className="flex items-center gap-1.5 text-xs">
              <ReportChangePill description={changeDescription} />
              {changeCaption && (
                <span className="truncate text-muted-foreground">{changeCaption}</span>
              )}
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
