import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

/** Nhãn trục X dài hơn thì cắt bớt; tên đầy đủ xem ở tooltip. */
const MAX_TICK_CHARS = 14
/** Khóa nội bộ giữ TỔNG phần cột của một hạng mục — có tiền tố để không trùng khóa chuỗi nào. */
const TOTAL_KEY = '__total'

/** Một chuỗi: khóa dữ liệu, nhãn chú giải, màu. */
export interface ComboSeries {
  key: string
  label: string
  color: string
}

/** Một hạng mục trên trục X: nhãn + giá trị từng chuỗi (cả phần cột lẫn đường) theo `ComboSeries.key`. */
export interface ComboDatum {
  label: string
  values: Record<string, number>
}

interface StackedColumnLineChartProps {
  data: ComboDatum[]
  /** Các phần của cột CHỒNG, vẽ từ chân lên đỉnh theo đúng thứ tự này. */
  bars: ComboSeries[]
  /** Đường vẽ CHUNG trục với cột — phải cùng đơn vị với cột (một trục, không bao giờ hai thang đo). */
  line: ComboSeries
  /** Đơn vị trong tooltip, vd "việc". */
  unit?: string
  height?: number
}

interface TooltipEntry {
  payload?: Record<string, number | string>
}

function ComboTooltip({
  active,
  payload,
  label,
  bars,
  line,
  unit,
}: {
  active?: boolean
  payload?: TooltipEntry[]
  label?: string | number
  bars: ComboSeries[]
  line: ComboSeries
  unit?: string
}) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload ?? {}
  const item = (s: ComboSeries) => (
    <li key={s.key} className="flex items-center gap-1.5 text-muted-foreground">
      <span aria-hidden className="size-2 shrink-0 rounded-full" style={{ backgroundColor: s.color }} />
      <span className="flex-1">{s.label}</span>
      <span className="font-medium text-foreground tabular-nums">{Number(row[s.key] ?? 0).toLocaleString('vi-VN')}</span>
    </li>
  )
  return (
    <div className="min-w-44 rounded-md border bg-popover px-3 py-2 text-popover-foreground shadow-md">
      <p className="text-sm font-semibold">{String(label ?? '')}</p>
      <ul className="mt-1 space-y-0.5 text-xs">{bars.map(item)}</ul>
      <p className="mt-0.5 flex justify-between text-xs text-muted-foreground">
        Cộng
        <span className="font-medium text-foreground tabular-nums">
          {Number(row[TOTAL_KEY] ?? 0).toLocaleString('vi-VN')}
          {unit ? ` ${unit}` : ''}
        </span>
      </p>
      <ul className="mt-1 border-t pt-1 text-xs">{item(line)}</ul>
    </div>
  )
}

/**
 * CỘT ĐỨNG CHỒNG + ĐƯỜNG trên MỘT trục: cột cho cơ cấu một đại lượng (vd việc đang mở, tách phần quá hạn), đường cho một
 * đại lượng CÙNG ĐƠN VỊ để đặt cạnh (vd việc xong trong kỳ) — nhìn một chỗ biết ai / dự án nào ôm nhiều mà làm ra ít.
 *
 * ⚠️ Không bao giờ hai trục Y: hai thang đo khác nhau làm hai đường cắt nhau ở chỗ tùy ý người vẽ, người đọc rút ra kết
 * luận sai. Đại lượng khác đơn vị (vd %) thì vẽ biểu đồ riêng.
 *
 * Chú giải luôn có (từ hai chuỗi trở lên màu không được là kênh duy nhất); chữ dùng token chữ, chấm màu đứng cạnh. Khe
 * 2px màu nền thẻ giữa các khúc cột; điểm của đường có viền 2px màu nền để nổi lên trên cột.
 */
export function StackedColumnLineChart({ data, bars, line, unit, height = 280 }: StackedColumnLineChartProps) {
  const rows = data.map((d) => {
    const row: Record<string, number | string> = { label: d.label }
    let total = 0
    for (const s of bars) {
      const value = d.values[s.key] ?? 0
      row[s.key] = value
      total += value
    }
    row[TOTAL_KEY] = total
    row[line.key] = d.values[line.key] ?? 0
    return row
  })
  const lastBar = bars.length - 1

  return (
    <div className="flex flex-1 flex-col gap-3">
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground" aria-label="Chú giải">
        {bars.map((s) => (
          <li key={s.key} className="flex items-center gap-1.5">
            <span aria-hidden className="size-2.5 shrink-0 rounded-sm" style={{ backgroundColor: s.color }} />
            {s.label}
          </li>
        ))}
        <li className="flex items-center gap-1.5">
          <span aria-hidden className="h-0.5 w-4 shrink-0 rounded-full" style={{ backgroundColor: line.color }} />
          {line.label}
        </li>
      </ul>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          {/*  Chỉ kẻ ngang, nhạt: lưới là chỗ dựa để đọc số, không phải nội dung. */}
          <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
          <XAxis
            dataKey="label"
            //  Ít mốc thì hiện đủ nhãn; nhiều mốc (30 ngày) thì để recharts tự bỏ bớt nhãn chen nhau, giữ nhãn đầu + cuối.
            interval={rows.length > 14 ? 'preserveStartEnd' : 0}
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
            tickFormatter={(value: string) =>
              value.length > MAX_TICK_CHARS ? `${value.slice(0, MAX_TICK_CHARS - 1)}…` : value
            }
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
            content={<ComboTooltip bars={bars} line={line} unit={unit} />}
          />
          {bars.map((s, index) => (
            <Bar
              key={s.key}
              dataKey={s.key}
              stackId="stack"
              fill={s.color}
              stroke="var(--card)"
              strokeWidth={2}
              maxBarSize={36}
              //  Bo 4px ở ĐỈNH cột (khúc trên cùng), chân cột vuông bám vạch gốc.
              radius={index === lastBar ? [4, 4, 0, 0] : 0}
              isAnimationActive={false}
            />
          ))}
          <Line
            type="linear"
            dataKey={line.key}
            stroke={line.color}
            strokeWidth={2}
            dot={{ r: 4, fill: line.color, stroke: 'var(--card)', strokeWidth: 2 }}
            activeDot={{ r: 5, fill: line.color, stroke: 'var(--card)', strokeWidth: 2 }}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
