import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { MonthComparisonPoint } from '../utils/report-period-comparison'

/** `current` rỗng = tháng chưa tới, đường kỳ này dừng ở đó. */
type ChartPoint = Omit<MonthComparisonPoint, 'current'> & { current: number | null }

const CURRENT_COLOR = 'var(--chart-1)'
/** Kỳ trước lùi về xám + nét đứt: nó là nền để so, không tranh chỗ với kỳ này. */
const PREVIOUS_COLOR = 'var(--chart-neutral)'

interface PeriodComparisonChartProps {
  data: ChartPoint[]
  currentLabel: string
  previousLabel: string
  /** Rút gọn số trên trục Y và trong tooltip. */
  formatValue: (value: number) => string
  height?: number
}

interface ComparisonTooltipProps {
  active?: boolean
  label?: string | number
  payload?: { payload?: ChartPoint }[]
  currentLabel: string
  previousLabel: string
  formatValue: (value: number) => string
}

/** Tooltip hiện CẢ HAI kỳ của tháng đang trỏ — so sánh là lý do biểu đồ tồn tại. */
function ComparisonTooltip({
  active,
  label,
  payload,
  currentLabel,
  previousLabel,
  formatValue,
}: ComparisonTooltipProps) {
  const point = payload?.[0]?.payload
  if (!active || !point) return null
  const rows = [
    { name: currentLabel, value: point.current, color: CURRENT_COLOR },
    { name: previousLabel, value: point.previous, color: PREVIOUS_COLOR },
  ].filter((row): row is { name: string; value: number; color: string } => row.value !== null)
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-popover-foreground shadow-md">
      <p className="mb-1 text-xs font-medium text-muted-foreground">Tháng {String(label).slice(1)}</p>
      {rows.map((row) => (
        <p key={row.name} className="flex items-center gap-2 text-sm">
          <span aria-hidden className="h-0.5 w-3 rounded-full" style={{ backgroundColor: row.color }} />
          <span className="text-muted-foreground">{row.name}</span>
          <span className="ml-auto pl-3 font-semibold tabular-nums">{formatValue(row.value)}</span>
        </p>
      ))}
    </div>
  )
}

/**
 * Đường so sánh HAI KỲ trên cùng trục 12 tháng — khối trung tâm của trang báo
 * cáo kiểu Haravan. Một trục Y duy nhất (cùng đơn vị tiền), không bao giờ hai.
 */
export function PeriodComparisonChart({
  data,
  currentLabel,
  previousLabel,
  formatValue,
  height = 280,
}: PeriodComparisonChartProps) {
  return (
    <div className="space-y-3">
      {/* Chú giải luôn có với hai chuỗi — màu không bao giờ là thứ duy nhất
          phân biệt: kỳ trước còn khác ở nét đứt. */}
      <ul className="flex flex-wrap gap-x-5 gap-y-1 text-sm">
        <li className="flex items-center gap-2">
          <span aria-hidden className="h-0.5 w-4 rounded-full" style={{ backgroundColor: CURRENT_COLOR }} />
          <span className="text-muted-foreground">{currentLabel}</span>
        </li>
        <li className="flex items-center gap-2">
          <span
            aria-hidden
            className="w-4 border-t-2 border-dashed"
            style={{ borderColor: PREVIOUS_COLOR }}
          />
          <span className="text-muted-foreground">{previousLabel}</span>
        </li>
      </ul>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
          />
          <YAxis
            width="auto"
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
            tickFormatter={(value: number) => formatValue(value)}
          />
          <Tooltip
            cursor={{ stroke: 'var(--muted-foreground)', strokeDasharray: '3 3' }}
            wrapperStyle={{ outline: 'none' }}
            content={
              <ComparisonTooltip
                currentLabel={currentLabel}
                previousLabel={previousLabel}
                formatValue={formatValue}
              />
            }
          />
          <Line
            type="monotone"
            dataKey="previous"
            stroke={PREVIOUS_COLOR}
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
            activeDot={{ r: 4, stroke: 'var(--card)', strokeWidth: 2 }}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="current"
            stroke={CURRENT_COLOR}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, stroke: 'var(--card)', strokeWidth: 2 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
