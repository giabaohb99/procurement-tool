import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { CHART_NEUTRAL } from '@/shared/ui/chart'

import type { ComparisonChartPoint } from './period-comparison-chart'

const CURRENT_COLOR = 'var(--chart-1)'

interface ReportFlexibleChartTimeBarsProps {
  data: ComparisonChartPoint[]
  currentLabel: string
  previousLabel: string
  /** `false` = không có kỳ so sánh (`compare=none`) — chỉ một dãy cột, không chú giải. */
  showPrevious: boolean
  formatValue: (value: number) => string
  allowDecimals: boolean
  tickCount?: number
}

interface TimeBarsTooltipProps {
  active?: boolean
  label?: string | number
  payload?: { payload?: ComparisonChartPoint }[]
  currentLabel: string
  previousLabel: string
  formatValue: (value: number) => string
}

function TimeBarsTooltip({
  active,
  label,
  payload,
  currentLabel,
  previousLabel,
  formatValue,
}: TimeBarsTooltipProps) {
  const point = payload?.[0]?.payload
  if (!active || !point) return null
  const rows = [
    { name: currentLabel, value: point.current, color: CURRENT_COLOR },
    { name: previousLabel, value: point.previous, color: CHART_NEUTRAL },
  ].filter((row): row is { name: string; value: number; color: string } => row.value !== null)
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-popover-foreground shadow-md">
      <p className="mb-1 text-xs font-medium text-muted-foreground">{String(label ?? '')}</p>
      {rows.map((row) => (
        <p key={row.name} className="flex items-center gap-2 text-sm">
          <span aria-hidden className="size-2.5 rounded-sm" style={{ backgroundColor: row.color }} />
          <span className="text-muted-foreground">{row.name}</span>
          <span className="ml-auto pl-3 font-semibold tabular-nums">{formatValue(row.value)}</span>
        </p>
      ))}
    </div>
  )
}

/**
 * Cột theo thời gian — kỳ này (màu chính) đứng cạnh kỳ so sánh (xám, lùi về nền). Thứ tự cột là
 * thứ tự thời gian, KHÔNG xếp lại theo độ lớn (khác cột theo nhóm).
 */
export function ReportFlexibleChartTimeBars({
  data,
  currentLabel,
  previousLabel,
  showPrevious,
  formatValue,
  allowDecimals,
  tickCount,
}: ReportFlexibleChartTimeBarsProps) {
  return (
    <div className="space-y-3">
      {showPrevious && (
        <ul className="flex flex-wrap gap-x-5 gap-y-1 text-sm">
          <li className="flex items-center gap-2">
            <span aria-hidden className="size-2.5 rounded-sm" style={{ backgroundColor: CURRENT_COLOR }} />
            <span className="text-muted-foreground">{currentLabel}</span>
          </li>
          <li className="flex items-center gap-2">
            <span aria-hidden className="size-2.5 rounded-sm" style={{ backgroundColor: CHART_NEUTRAL }} />
            <span className="text-muted-foreground">{previousLabel}</span>
          </li>
        </ul>
      )}
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} barGap={2}>
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
          />
          <YAxis
            allowDecimals={allowDecimals}
            tickCount={tickCount}
            width="auto"
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
            tickFormatter={(value: number) => formatValue(value)}
          />
          <Tooltip
            cursor={{ fill: 'var(--row-hover)' }}
            wrapperStyle={{ outline: 'none' }}
            content={
              <TimeBarsTooltip
                currentLabel={currentLabel}
                previousLabel={previousLabel}
                formatValue={formatValue}
              />
            }
          />
          {showPrevious && (
            <Bar
              dataKey="previous"
              name={previousLabel}
              fill={CHART_NEUTRAL}
              radius={[4, 4, 0, 0]}
              maxBarSize={28}
              isAnimationActive={false}
            />
          )}
          <Bar
            dataKey="current"
            name={currentLabel}
            fill={CURRENT_COLOR}
            radius={[4, 4, 0, 0]}
            maxBarSize={28}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
