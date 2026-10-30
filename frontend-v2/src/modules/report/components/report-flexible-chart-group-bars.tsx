import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { CHART_NEUTRAL, ChartTooltipContent } from '@/shared/ui/chart'
import { cn } from '@/shared/utils/cn'

import { FLEXIBLE_CHART_BAR_COLOR } from '../utils/report-flexible-chart-colors'
import type { FlexibleGroupItem } from '../utils/report-flexible-chart-series'

/** Chiều cao một dòng cột ngang — quyết định chiều cao cả biểu đồ (như `HorizontalBarChart`). */
const ROW_HEIGHT = 36
const MAX_TICK_CHARS = 24
/** Cột dọc đông hơn ngần này thì nhãn trục X nghiêng cho khỏi đè nhau. */
const VERTICAL_TILT_AFTER = 6

function truncateLabel(value: string): string {
  return value.length > MAX_TICK_CHARS ? `${value.slice(0, MAX_TICK_CHARS - 1)}…` : value
}

/** Trục số phải chứa cả số âm (vd "Thay đổi ròng") — mặc định `[0, dataMax]` sẽ cắt mất. */
const VALUE_DOMAIN: [(min: number) => number, (max: number) => number] = [
  (min) => Math.min(0, min),
  (max) => Math.max(0, max),
]

interface ReportFlexibleChartGroupBarsProps {
  items: FlexibleGroupItem[]
  orientation: 'horizontal' | 'vertical'
  formatValue: (value: number) => string
  /** Bấm một cột của nhóm THẬT (không phải "Khác"). Bỏ trống = biểu đồ chỉ để xem. */
  onSelectItem?: (item: FlexibleGroupItem) => void
}

/**
 * Cột theo nhóm "Xem theo", đã xếp lớn → nhỏ ở `buildFlexibleGroupSeries`. Một màu cho mọi cột
 * (độ dài đã nói độ lớn); "Khác" xám trung tính vì nó không phải một nhóm thật.
 */
export function ReportFlexibleChartGroupBars({
  items,
  orientation,
  formatValue,
  onSelectItem,
}: ReportFlexibleChartGroupBarsProps) {
  const horizontal = orientation === 'horizontal'
  const tilt = !horizontal && items.length > VERTICAL_TILT_AFTER
  const handleClick = onSelectItem
    ? (_bar: unknown, index: number) => {
        const item = items[index]
        if (item && !item.isRest) onSelectItem(item)
      }
    : undefined

  const bar = (
    <Bar
      dataKey="value"
      radius={horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]}
      maxBarSize={horizontal ? 20 : 36}
      isAnimationActive={false}
      onClick={handleClick}
    >
      {items.map((item) => (
        <Cell
          key={item.key}
          fill={item.isRest ? CHART_NEUTRAL : FLEXIBLE_CHART_BAR_COLOR}
          className={cn(onSelectItem && !item.isRest && 'cursor-pointer')}
        />
      ))}
      <LabelList
        dataKey="value"
        position={horizontal ? 'right' : 'top'}
        offset={6}
        fill="var(--foreground)"
        fontSize={12}
        formatter={(value) => formatValue(Number(value)).replace(/ /g, '\u00a0')}
      />
    </Bar>
  )

  const tooltip = (
    <Tooltip
      cursor={{ fill: 'var(--row-hover)' }}
      wrapperStyle={{ outline: 'none' }}
      content={<ChartTooltipContent formatValue={formatValue} />}
    />
  )

  if (horizontal) {
    return (
      //  "Tất cả" ở chiều Nhân sự có thể ra vài trăm dòng — trần cao + cuộn trong thẻ, không
      //  để thẻ dài hết trang đẩy bảng "Xem theo" xuống tít dưới.
      <div className="max-h-[640px] overflow-y-auto">
        <ResponsiveContainer width="100%" height={items.length * ROW_HEIGHT + 8}>
          <BarChart
            data={items}
            layout="vertical"
            margin={{ top: 4, right: 72, bottom: 4, left: 0 }}
            barCategoryGap={8}
          >
            <XAxis type="number" hide domain={VALUE_DOMAIN} />
            <YAxis
              type="category"
              dataKey="label"
              width="auto"
              interval={0}
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
              tickFormatter={truncateLabel}
            />
            {tooltip}
            {bar}
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={tilt ? 340 : 300}>
      <BarChart data={items} margin={{ top: 20, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
        <XAxis
          dataKey="label"
          interval={0}
          tickLine={false}
          axisLine={false}
          height={tilt ? 80 : 30}
          angle={tilt ? -35 : 0}
          textAnchor={tilt ? 'end' : 'middle'}
          tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
          tickFormatter={truncateLabel}
        />
        <YAxis
          width="auto"
          domain={VALUE_DOMAIN}
          tickLine={false}
          axisLine={false}
          tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
          tickFormatter={(value: number) => formatValue(value)}
        />
        {tooltip}
        {bar}
      </BarChart>
    </ResponsiveContainer>
  )
}
