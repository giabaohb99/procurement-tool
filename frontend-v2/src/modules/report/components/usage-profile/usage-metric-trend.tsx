import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { ChartTooltipContent } from '@/shared/ui/chart'

import type { UsageMetricTrendPoint } from '../../types/usage-metric-catalog'
import { formatUsageValue } from '../../utils/usage-format'
import { unitKind } from '../../utils/usage-metric-catalog-helpers'
import { buildTrendData } from '../../utils/usage-metric-chart-helpers'

interface Props {
  points: UsageMetricTrendPoint[]
  unit: string
}

/** Trung vị công ty theo tuần (tối đa 8 tuần gần nhất). Tuần không ai đo được để trống, đường đứt đoạn. */
export function UsageMetricTrend({ points, unit }: Props) {
  const data = buildTrendData(points)
  const format = (v: number) => formatUsageValue(v, unitKind(unit))
  //  Trục dọc cố định đáy 0: tỷ lệ luôn 0-100%; còn lại tối thiểu tới 1. Không chặn thì toàn trung vị 0 làm recharts
  //  tự chọn 0-4 → tỷ lệ hiện «0% · 200% · 400%» (thử tay 20/10).
  const domain: [number, number | ((max: number) => number)] = unit === 'ratio' ? [0, 1] : [0, (max: number) => Math.max(1, max)]
  return (
    <ResponsiveContainer width="100%" height={120}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
        <XAxis dataKey="label" tickLine={false} axisLine={false} padding={{ left: 12, right: 12 }} tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} />
        <YAxis width="auto" domain={domain} tickLine={false} axisLine={false} tickFormatter={format} tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} />
        <Tooltip wrapperStyle={{ outline: 'none' }} content={<ChartTooltipContent formatValue={format} />} />
        <Line dataKey="value" stroke="var(--chart-2)" strokeWidth={2} dot={{ r: 3, fill: 'var(--chart-2)' }} activeDot={{ r: 4 }} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
