/**
 * duoc-CR-784 — biểu đồ "Diễn biến đơn giá qua các lần mua" (bản mẫu `renderLast5`): một đường theo thứ tự các lần mua CÓ GIÁ
 * của đúng một mã, cũ → mới. Chỉ vẽ khi máy chủ trả `series` (đúng một mã được chọn).
 *
 * Trục giá KHÔNG bắt đầu từ 0 (xem `priceAxisDomain`) và mỗi lần mua là một chấm — giá đi ngang vài tháng rồi nhích 3% vẫn
 * nhìn ra. Cỡ chữ cố định vì recharts vẽ theo điểm ảnh thật. Màu theo token `--chart-1` (sáng / tối tự đổi).
 */
import { useMemo } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { formatQuantity } from '@/shared/utils/format-money'

import type { PackagingHistoryPoint } from '../types/packaging-cost-types'
import {
  buildChartPoints,
  priceAxisDomain,
  type HistoryChartPoint,
} from '../utils/packaging-history'
import { formatPackagingPrice } from '../utils/packaging-price-format'

const AXIS_TICK = { fontSize: 11, fill: 'var(--muted-foreground)' }
const Y_AXIS_WIDTH = 64

interface PackagingHistoryChartProps {
  series: readonly PackagingHistoryPoint[]
  /** Mã · tên của mã đang xem — in cạnh tiêu đề vì bảng một mã không còn cột tên. */
  subject?: string
  className?: string
}

function PointTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: { payload?: HistoryChartPoint }[]
}) {
  const point = payload?.[0]?.payload
  if (!active || !point) return null
  return (
    <div className="min-w-44 rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md">
      <p className="mb-1 text-sm font-semibold">{point.label}</p>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 tabular-nums">
        <dt className="text-muted-foreground">Đơn giá</dt>
        <dd className="text-right font-semibold">{formatPackagingPrice(point.price)}</dd>
        <dt className="text-muted-foreground">Số lượng</dt>
        <dd className="text-right">{formatQuantity(point.qty) || '—'}</dd>
        <dt className="text-muted-foreground">Nhà cung cấp</dt>
        <dd className="max-w-48 truncate text-right">{point.supplier || '—'}</dd>
      </dl>
    </div>
  )
}

export function PackagingHistoryChart({ series, subject, className }: PackagingHistoryChartProps) {
  const points = useMemo(() => buildChartPoints(series), [series])
  const domain = useMemo(() => priceAxisDomain(series.map((point) => point.price)), [series])
  return (
    <div className={className}>
      <p className="mb-1 text-sm font-medium">
        Diễn biến đơn giá qua các lần mua{subject && ` — ${subject}`}{' '}
        <span className="font-normal text-muted-foreground">({series.length} lần có giá)</span>
      </p>
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={points} margin={{ top: 6, right: 16, bottom: 4, left: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tick={AXIS_TICK}
            interval="preserveStartEnd"
          />
          <YAxis
            width={Y_AXIS_WIDTH}
            tickLine={false}
            axisLine={false}
            tick={AXIS_TICK}
            domain={domain}
            tickFormatter={(value: number) => formatPackagingPrice(value)}
          />
          <Tooltip
            wrapperStyle={{ outline: 'none' }}
            cursor={{ stroke: 'var(--border)' }}
            content={<PointTooltip />}
          />
          <Line
            dataKey="price"
            stroke="var(--chart-1)"
            strokeWidth={2}
            dot={{ r: 3, fill: 'var(--chart-1)', stroke: 'var(--card)' }}
            activeDot={{ r: 5 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
