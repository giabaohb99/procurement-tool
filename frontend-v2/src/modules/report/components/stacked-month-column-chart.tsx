import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export interface StackedSeries<K extends string> {
  key: K
  label: string
  color: string
}

interface StackedMonthColumnChartProps<K extends string> {
  data: ({ label: string } & Record<K, number>)[]
  /** Thứ tự = thứ tự CHỒNG từ chân lên đỉnh. Tối đa vài chuỗi, màu gán cố định. */
  series: StackedSeries<K>[]
  unit?: string
  height?: number
}

interface StackTooltipProps {
  active?: boolean
  label?: string | number
  payload?: { dataKey?: unknown; value?: unknown }[]
  series: { key: string; label: string; color: string }[]
  unit?: string
}

/** Tooltip liệt kê từng chuỗi + tổng — chồng cột thì đỉnh không đọc ra được từng phần. */
function StackTooltip({ active, label, payload, series, unit }: StackTooltipProps) {
  if (!active || !payload?.length) return null
  const value = (key: string) => Number(payload.find((p) => p.dataKey === key)?.value ?? 0)
  const total = series.reduce((sum, s) => sum + value(s.key), 0)
  const fmt = (n: number) => `${n.toLocaleString('vi-VN')}${unit ? ` ${unit}` : ''}`
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-popover-foreground shadow-md">
      <p className="mb-1 text-xs font-medium text-muted-foreground">Tháng {String(label).slice(1)}</p>
      {[...series].reverse().map((s) => (
        <p key={s.key} className="flex items-center gap-2 text-sm">
          <span aria-hidden className="size-2.5 rounded-sm" style={{ backgroundColor: s.color }} />
          <span className="text-muted-foreground">{s.label}</span>
          <span className="ml-auto pl-3 font-semibold tabular-nums">{fmt(value(s.key))}</span>
        </p>
      ))}
      <p className="mt-1 flex border-t pt-1 text-sm">
        <span className="text-muted-foreground">Tổng</span>
        <span className="ml-auto pl-3 font-semibold tabular-nums">{fmt(total)}</span>
      </p>
    </div>
  )
}

/**
 * Cột CHỒNG theo tháng — mỗi cột là tổng, các khúc là phần của từng chuỗi.
 * Chú giải luôn có (≥ 2 chuỗi), khe 2px màu nền tách các khúc.
 */
export function StackedMonthColumnChart<K extends string>({
  data,
  series,
  unit,
  height = 280,
}: StackedMonthColumnChartProps<K>) {
  return (
    <div className="space-y-3">
      <ul className="flex flex-wrap gap-x-5 gap-y-1 text-sm">
        {series.map((s) => (
          <li key={s.key} className="flex items-center gap-2">
            <span aria-hidden className="size-2.5 rounded-sm" style={{ backgroundColor: s.color }} />
            <span className="text-muted-foreground">{s.label}</span>
          </li>
        ))}
      </ul>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis
            dataKey="label"
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
          />
          <YAxis
            width="auto"
            allowDecimals={false}
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
          />
          <Tooltip
            cursor={{ fill: 'var(--row-hover)' }}
            wrapperStyle={{ outline: 'none' }}
            content={<StackTooltip series={series} unit={unit} />}
          />
          {series.map((s, i) => (
            <Bar
              key={s.key}
              dataKey={s.key}
              stackId="stack"
              fill={s.color}
              stroke="var(--card)"
              strokeWidth={1}
              maxBarSize={36}
              // Chỉ khúc trên cùng bo đầu; chân cột bám vạch gốc nên vuông.
              radius={i === series.length - 1 ? [4, 4, 0, 0] : 0}
              isAnimationActive={false}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
