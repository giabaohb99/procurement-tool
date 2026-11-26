/**
 * duoc-CR-784 — biểu đồ "Diễn biến đơn giá theo thành phần" của Lịch sử mua hàng chế độ sản phẩm khi chọn ĐÚNG MỘT sản phẩm:
 * mỗi mã thành phần của định mức (chai, nắp, nhãn, nhãn thùng, thùng — mã nào có lần mua có giá) một đường giá cũ → mới, chú giải
 * = vai trò + mã. Cùng cách vẽ với biểu đồ một mã (`packaging-history-chart.tsx`): trục giá không bắt đầu từ 0, mỗi lần mua là
 * một chấm, cỡ chữ cố định, màu theo token biểu đồ. Chỉ vẽ khi máy chủ trả `series_by_code`.
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

import type { PackagingHistorySeriesLine } from '../types/packaging-cost-types'
import {
  assignHistoryLineStyles,
  buildSeriesRows,
  historyLineKey,
  historyLineLegend,
  seriesAxisDomain,
  type HistoryLineStyle,
  type HistorySeriesRow,
} from '../utils/packaging-history-series'
import { formatPackagingPrice } from '../utils/packaging-price-format'

const AXIS_TICK = { fontSize: 11, fill: 'var(--muted-foreground)' }
const Y_AXIS_WIDTH = 64

interface PackagingHistoryCodeChartProps {
  lines: readonly PackagingHistorySeriesLine[]
  /** Mã · tên sản phẩm đang xem. */
  subject?: string
  className?: string
}

/** Mẫu màu của một đường (nét đứt vẽ bằng gạch ngắn) — dùng chung cho chú giải và ô rê chuột. */
function Swatch({ style }: { style: HistoryLineStyle }) {
  return (
    <svg width="18" height="8" aria-hidden className="shrink-0">
      <line
        x1="0"
        x2="18"
        y1="4"
        y2="4"
        stroke={style.css}
        strokeWidth="2.5"
        strokeDasharray={style.dash || undefined}
      />
    </svg>
  )
}

function CodeTooltip({
  active,
  payload,
  lines,
  styles,
}: {
  active?: boolean
  payload?: { payload?: HistorySeriesRow }[]
  lines: readonly PackagingHistorySeriesLine[]
  styles: readonly HistoryLineStyle[]
}) {
  const row = payload?.[0]?.payload
  if (!active || !row) return null
  const present = lines.flatMap((line, index) => {
    const price = row[historyLineKey(index)]
    return typeof price === 'number' ? [{ line, index, price }] : []
  })
  return (
    <div className="min-w-44 rounded-md border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md">
      <p className="mb-1 text-sm font-semibold">{row.label}</p>
      <dl className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-0.5 tabular-nums">
        {present.map(({ line, index, price }) => (
          <div key={line.code} className="col-span-2 grid grid-cols-subgrid items-center">
            <dt className="flex items-center gap-1.5 text-muted-foreground">
              <Swatch style={styles[index]} />
              {historyLineLegend(line)}
            </dt>
            <dd className="text-right font-semibold">{formatPackagingPrice(price)}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

export function PackagingHistoryCodeChart({ lines, subject, className }: PackagingHistoryCodeChartProps) {
  const rows = useMemo(() => buildSeriesRows(lines), [lines])
  const domain = useMemo(() => seriesAxisDomain(lines), [lines])
  const styles = useMemo(() => assignHistoryLineStyles(lines), [lines])
  return (
    <div className={className}>
      <p className="mb-1 text-sm font-medium">
        Diễn biến đơn giá theo thành phần (VNĐ){subject && ` — ${subject}`}
      </p>
      <ul className="mb-1 flex flex-wrap gap-x-4 gap-y-1 text-xs" aria-label="Chú giải">
        {lines.map((line, index) => (
          <li key={line.code} className="flex items-center gap-1.5" title={line.name || undefined}>
            <Swatch style={styles[index]} />
            {historyLineLegend(line)}
          </li>
        ))}
      </ul>
      <ResponsiveContainer width="100%" height={170}>
        <LineChart data={rows} margin={{ top: 6, right: 16, bottom: 4, left: 0 }}>
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
            content={<CodeTooltip lines={lines} styles={styles} />}
          />
          {lines.map((line, index) => (
            <Line
              key={line.code}
              name={historyLineLegend(line)}
              dataKey={historyLineKey(index)}
              stroke={styles[index].css}
              strokeWidth={2}
              strokeDasharray={styles[index].dash || undefined}
              connectNulls
              dot={{ r: 3, fill: styles[index].css, stroke: 'var(--card)' }}
              activeDot={{ r: 5 }}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
