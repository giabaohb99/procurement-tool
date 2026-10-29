import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

import { ChartTooltipContent } from '@/shared/ui/chart'
import { cn } from '@/shared/utils/cn'

import { pickDonutColor } from '../utils/report-flexible-chart-colors'
import type { FlexibleGroupItem } from '../utils/report-flexible-chart-series'

interface ReportFlexibleChartDonutProps {
  items: FlexibleGroupItem[]
  formatValue: (value: number) => string
  /** Bấm một lát / một dòng chú giải của nhóm THẬT. Bỏ trống = chỉ để xem. */
  onSelectItem?: (item: FlexibleGroupItem) => void
}

/**
 * Vành khuyên tỷ trọng theo nhóm — chỉ được chọn khi `canDrawDonut` (≤ 6 nhóm có số, không âm,
 * không phải tỷ lệ). Chú giải là các NÚT khi bấm được: đường vào bằng bàn phím của «bấm lát mở
 * danh sách», vì lát bánh của recharts không nhận Tab.
 */
export function ReportFlexibleChartDonut({
  items,
  formatValue,
  onSelectItem,
}: ReportFlexibleChartDonutProps) {
  const total = items.reduce((sum, item) => sum + item.value, 0)
  const clickable = (item: FlexibleGroupItem) => !!onSelectItem && !item.isRest

  return (
    <div className="grid items-center gap-4 sm:grid-cols-[minmax(0,240px)_1fr]">
      <div className="relative">
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={items}
              dataKey="value"
              nameKey="label"
              cx="50%"
              cy="50%"
              innerRadius={62}
              outerRadius={96}
              //  Viền màu nền = khe hở 2px tách hai lát.
              stroke="var(--card)"
              strokeWidth={2}
              isAnimationActive={false}
              onClick={(_slice, index) => {
                const item = items[index]
                if (item && clickable(item)) onSelectItem?.(item)
              }}
            >
              {items.map((item, index) => (
                <Cell
                  key={item.key}
                  fill={pickDonutColor(item, index)}
                  className={cn(clickable(item) && 'cursor-pointer')}
                />
              ))}
            </Pie>
            <Tooltip
              wrapperStyle={{ outline: 'none' }}
              content={<ChartTooltipContent formatValue={formatValue} />}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="max-w-[110px] truncate text-center text-xl font-semibold text-navy dark:text-foreground">
            {formatValue(total)}
          </span>
          <span className="text-xs text-muted-foreground">Tổng</span>
        </div>
      </div>

      <ul className="min-w-0 space-y-1">
        {items.map((item, index) => {
          const share = total > 0 ? `${Math.round((item.value / total) * 100)}%` : '0%'
          const body = (
            <>
              <span
                aria-hidden
                className="size-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: pickDonutColor(item, index) }}
              />
              <span className="min-w-0 flex-1 truncate text-left text-muted-foreground" title={item.label}>
                {item.label}
              </span>
              <span className="shrink-0 font-medium tabular-nums">{formatValue(item.value)}</span>
              <span className="w-10 shrink-0 text-right tabular-nums text-muted-foreground">{share}</span>
            </>
          )
          return (
            <li key={item.key}>
              {clickable(item) ? (
                <button
                  type="button"
                  className="flex w-full items-center gap-2 rounded-md px-1.5 py-1 text-sm hover:bg-row-hover focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                  aria-label={`Xem danh sách ${item.label} từ biểu đồ`}
                  onClick={() => onSelectItem?.(item)}
                >
                  {body}
                </button>
              ) : (
                <div className="flex items-center gap-2 px-1.5 py-1 text-sm">{body}</div>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}
