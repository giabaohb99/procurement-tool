import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { BarList, type BarListItem } from '@/shared/ui/bar-list'
import { ChartCard } from '@/shared/ui/chart'

import type { SystemLogSummary } from '../api/system-log-api'
import { formatHourLabel, spansMultipleDays } from '../utils/system-log-format'

interface SystemLogSummaryChartsProps {
  summary?: SystemLogSummary
  loading: boolean
  /** Hai đầu khoảng lọc — quyết định trục X có kèm ngày hay không. */
  from: string
  to: string
  /** Bấm vào một cột giờ: chỗ gọi tự siết khoảng lọc về đúng giờ đó. */
  onPickHour?: (hour: string) => void
}

/**
 * Ba biểu đồ tóm tắt của màn nhật ký hệ thống (bao-CR-407, §8.2).
 *
 * Chúng trả lời ba câu khác nhau: *«lúc nào đông và lúc nào hỏng»* ·
 * *«đường nào bị gọi nhiều»* · *«hỏng vì mã lỗi gì»*. Cùng một bộ lọc với bảng
 * bên dưới — lọc bảng mà biểu đồ vẫn toàn hệ thì người đọc so hai thứ không so
 * được với nhau.
 */
export function SystemLogSummaryCharts({
  summary,
  loading,
  from,
  to,
  onPickHour,
}: SystemLogSummaryChartsProps) {
  const withDay = spansMultipleDays(from, to)

  //  Tách phần CHẠY ĐƯỢC ra khỏi phần LỖI để xếp chồng: cột cao = tổng lượt gọi,
  //  khúc đỏ dưới chân = phần hỏng. Vẽ hai cột cạnh nhau thì lỗi (thường một vài
  //  lượt trên hàng nghìn) lùn tới mức không thấy.
  const hourData = (summary?.by_hour ?? []).map((row) => ({
    label: formatHourLabel(row.hour, withDay),
    hour: row.hour,
    errors: row.errors,
    ok: Math.max(0, row.total - row.errors),
    total: row.total,
  }))

  const routeItems: BarListItem[] = (summary?.by_route ?? []).map((row) => ({
    //  Đường ĐÃ GOM (`/api/purchase-orders/{id}`), không phải đường thật — gom
    //  theo đường thật thì mỗi phiếu một dòng và bảng xếp hạng thành vô nghĩa.
    label: row.route || '(không rõ)',
    value: row.total,
    color: row.failed > 0 ? 'var(--warning)' : 'var(--chart-1)',
  }))

  const errorItems: BarListItem[] = (summary?.by_error ?? []).map((row) => ({
    label: row.error_code || '(không mã)',
    value: row.total,
    color: 'var(--destructive)',
  }))

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <ChartCard
        title="Lượt gọi theo giờ"
        description="Cột là tổng lượt gọi; khúc đỏ là phần lỗi hoặc bị chặn"
        loading={loading}
        isEmpty={hourData.length === 0}
        emptyLabel="Không có lượt gọi nào trong khoảng đã lọc."
        className="lg:col-span-2"
      >
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={hourData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
            <XAxis
              dataKey="label"
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
              tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
            />
            <YAxis
              width="auto"
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
              tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
            />
            <Tooltip
              cursor={{ fill: 'var(--row-hover)' }}
              wrapperStyle={{ outline: 'none' }}
              content={<HourTooltip />}
            />
            <Bar
              dataKey="errors"
              stackId="calls"
              fill="var(--destructive)"
              maxBarSize={36}
              onClick={onPickHour ? (_bar, index) => onPickHour(hourData[index]?.hour ?? '') : undefined}
              className={onPickHour ? 'cursor-pointer' : undefined}
            />
            <Bar
              dataKey="ok"
              stackId="calls"
              fill="var(--chart-1)"
              radius={[4, 4, 0, 0]}
              maxBarSize={36}
              onClick={onPickHour ? (_bar, index) => onPickHour(hourData[index]?.hour ?? '') : undefined}
              className={onPickHour ? 'cursor-pointer' : undefined}
            />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <div className="grid gap-4">
        <ChartCard
          title="Đường bị gọi nhiều nhất"
          description="Thanh vàng là đường có lượt hỏng"
          loading={loading}
          isEmpty={routeItems.length === 0}
        >
          <BarList items={routeItems} />
        </ChartCard>

        <ChartCard
          title="Mã lỗi"
          description="Chỉ đếm lượt gọi có mã lỗi"
          loading={loading}
          isEmpty={errorItems.length === 0}
          emptyLabel="Không có lỗi nào trong khoảng đã lọc."
        >
          <BarList items={errorItems} />
        </ChartCard>
      </div>
    </div>
  )
}

interface HourTooltipProps {
  active?: boolean
  payload?: { payload?: { label?: string; total?: number; errors?: number } }[]
}

/**
 * Tooltip riêng cho cột xếp chồng.
 *
 * `ChartTooltipContent` dùng chung chỉ đọc `payload[0]` — ở đây phần tử đầu là
 * khúc LỖI, nên dùng nó thì rê chuột lên cột nào cũng chỉ thấy số lỗi và người
 * đọc tưởng đó là tổng.
 */
function HourTooltip({ active, payload }: HourTooltipProps) {
  const datum = payload?.[0]?.payload
  if (!active || !datum) return null

  const errors = datum.errors ?? 0

  return (
    <div className="rounded-md border bg-popover px-3 py-2 text-popover-foreground shadow-md">
      <p className="text-sm font-semibold tabular-nums">
        {(datum.total ?? 0).toLocaleString('vi-VN')} lượt gọi
      </p>
      <p className="mt-0.5 text-xs text-muted-foreground">{datum.label}</p>
      {errors > 0 && (
        <p className="mt-1 text-xs font-medium text-destructive tabular-nums">
          {errors.toLocaleString('vi-VN')} lỗi / bị chặn
        </p>
      )}
    </div>
  )
}
