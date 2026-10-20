import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import type { UsageMetricBucket } from '../../types/usage-metric-catalog'
import { buildHistogramData, medianBucketIndex, type HistogramDatum } from '../../utils/usage-metric-chart-helpers'

interface Props {
  buckets: UsageMetricBucket[]
  unit: string
  median: number | null
  /** Chữ trên vạch trung vị, vd «Trung vị 5». */
  medianText: string
}

interface TipProps {
  active?: boolean
  payload?: { payload: HistogramDatum }[]
}

function HistogramTip({ active, payload }: TipProps) {
  const d = payload?.[0]?.payload
  if (!active || !d) return null
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-popover-foreground shadow-md">
      <p className="text-sm font-semibold tabular-nums">{d.value.toLocaleString('vi-VN')} người</p>
      <p className="mt-0.5 text-xs text-muted-foreground">{d.range}</p>
    </div>
  )
}

/** Phân phối số người theo khoảng giá trị của tuần mới nhất, kèm vạch đứng ở trung vị công ty. */
export function UsageMetricHistogram({ buckets, unit, median, medianText }: Props) {
  const data = buildHistogramData(buckets, unit)
  const idx = medianBucketIndex(buckets, median)
  return (
    <ResponsiveContainer width="100%" height={150}>
      <BarChart data={data} margin={{ top: 16, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
        <XAxis dataKey="label" tickLine={false} axisLine={false} interval="preserveStartEnd" tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} />
        <YAxis width="auto" allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} />
        <Tooltip cursor={{ fill: 'var(--row-hover)' }} wrapperStyle={{ outline: 'none' }} content={<HistogramTip />} />
        <Bar dataKey="value" fill="var(--chart-1)" radius={[3, 3, 0, 0]} maxBarSize={32} />
        {idx >= 0 && (
          <ReferenceLine
            x={data[idx].label}
            stroke="var(--foreground)"
            strokeDasharray="4 3"
            label={{ value: medianText, position: 'top', fill: 'var(--foreground)', fontSize: 11 }}
          />
        )}
      </BarChart>
    </ResponsiveContainer>
  )
}
