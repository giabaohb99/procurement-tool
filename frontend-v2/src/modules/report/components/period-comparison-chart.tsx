import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

/**
 * Một mốc trên biểu đồ so sánh hai kỳ — TỔNG QUÁT, không phụ thuộc trục thời
 * gian cụ thể nào (tháng, ngày, tuần…): dùng chung cho trang Tổng quan Thu mua
 * (mốc = tháng) lẫn khung báo cáo Haravan (`ReportTrendChart`, mốc theo
 * `meta.dimensions`/`period.granularity` của từng báo cáo).
 *
 * `null` = mốc không có số: kỳ này đang chạy dở (tháng/ngày chưa tới) thì
 * đường VẼ dừng ở đó; kỳ so sánh thiếu mốc (so `year`, hai kỳ lệch độ dài) thì
 * điểm đó bị bỏ khỏi tooltip.
 */
export interface ComparisonChartPoint {
  label: string
  current: number | null
  previous: number | null
}

type ChartPoint = ComparisonChartPoint

const CURRENT_COLOR = 'var(--chart-1)'
/** Kỳ trước lùi về xám + nét đứt: nó là nền để so, không tranh chỗ với kỳ này. */
const PREVIOUS_COLOR = 'var(--chart-neutral)'

interface PeriodComparisonChartProps {
  data: ChartPoint[]
  currentLabel: string
  previousLabel: string
  /** Rút gọn số trên trục Y và trong tooltip. */
  formatValue: (value: number) => string
  /**
   * Đổi chữ tiêu đề mốc trong tooltip — mặc định hiện NGUYÊN `label` của điểm.
   *
   * Báo cáo Haravan (`ReportTrendChart`) nhận nhãn ĐỌC ĐƯỢC thẳng từ backend
   * (`meta`/`trend[].label`, vd "01/09", "Tuần 36") nên bỏ trống là đủ; giữ tùy
   * chọn này cho trang nào sau này cần đổi nhãn mốc kiểu viết tắt (vd "T9").
   */
  formatLabel?: (label: string) => string
  /** `false` cho chỉ số ĐẾM — không thì trục số nhỏ ra vạch lẻ bị làm tròn trùng nhau ("2, 2, 1"). */
  allowDecimals?: boolean
  /** Số vạch trục Y — bỏ trống để recharts tự chọn (mặc định 5). */
  tickCount?: number
  height?: number
}

interface ComparisonTooltipProps {
  active?: boolean
  label?: string | number
  payload?: { payload?: ChartPoint }[]
  currentLabel: string
  previousLabel: string
  formatValue: (value: number) => string
  formatLabel: (label: string) => string
}

/** Tooltip hiện CẢ HAI kỳ của mốc đang trỏ — so sánh là lý do biểu đồ tồn tại. */
function ComparisonTooltip({
  active,
  label,
  payload,
  currentLabel,
  previousLabel,
  formatValue,
  formatLabel,
}: ComparisonTooltipProps) {
  const point = payload?.[0]?.payload
  if (!active || !point) return null
  const rows = [
    { name: currentLabel, value: point.current, color: CURRENT_COLOR },
    { name: previousLabel, value: point.previous, color: PREVIOUS_COLOR },
  ].filter((row): row is { name: string; value: number; color: string } => row.value !== null)
  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-popover-foreground shadow-md">
      <p className="mb-1 text-xs font-medium text-muted-foreground">
        {formatLabel(String(label ?? ''))}
      </p>
      {rows.map((row) => (
        <p key={row.name} className="flex items-center gap-2 text-sm">
          <span
            aria-hidden
            className="h-0.5 w-3 rounded-full"
            style={{ backgroundColor: row.color }}
          />
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
  formatLabel = (label) => label,
  allowDecimals = true,
  tickCount,
  height = 280,
}: PeriodComparisonChartProps) {
  //  `linear` thay `monotone`: đường cong làm tháng 0 → 1 → 0 thành một quả
  //  chuông mượt, như thể số liệu tăng giảm dần qua từng ngày (đại ca chê
  //  01/10/2026). Ít mốc (≤ 16, vd 12 tháng) thì chấm từng mốc để người xem
  //  biết đâu là số thật, đâu là đoạn nối.
  const showDots = data.length <= 16
  return (
    <div className="space-y-3">
      {/* Chú giải luôn có với hai chuỗi — màu không bao giờ là thứ duy nhất
          phân biệt: kỳ trước còn khác ở nét đứt. */}
      <ul className="flex flex-wrap gap-x-5 gap-y-1 text-sm">
        <li className="flex items-center gap-2">
          <span
            aria-hidden
            className="h-0.5 w-4 rounded-full"
            style={{ backgroundColor: CURRENT_COLOR }}
          />
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
            allowDecimals={allowDecimals}
            tickCount={tickCount}
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
                formatLabel={formatLabel}
              />
            }
          />
          <Line
            type="linear"
            dataKey="previous"
            stroke={PREVIOUS_COLOR}
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
            activeDot={{ r: 4, stroke: 'var(--card)', strokeWidth: 2 }}
            isAnimationActive={false}
          />
          <Line
            type="linear"
            dataKey="current"
            stroke={CURRENT_COLOR}
            strokeWidth={2}
            dot={showDots ? { r: 3, fill: CURRENT_COLOR, strokeWidth: 0 } : false}
            activeDot={{ r: 4, stroke: 'var(--card)', strokeWidth: 2 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
