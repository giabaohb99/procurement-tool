import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

import { ChartLegendItem, ChartTooltipContent, type ChartDatum } from './chart'

const CHART_HEIGHT = 180

/** Một lát bánh: nhãn, giá trị và MÀU ĐÃ CHỐT theo hạng mục (không theo thứ hạng). */
export interface DonutSlice extends ChartDatum {
  color: string
}

interface DonutChartProps {
  data: DonutSlice[]
  /** Chữ nhỏ dưới con số ở giữa vòng, vd "nhân sự". */
  centerLabel: string
  unit?: string
  /**
   * Định dạng số ở CHÍNH GIỮA vòng. Mặc định là số nguyên theo locale — với
   * số tiền hàng tỉ thì phải rút gọn ("1,7 tỷ"), để nguyên sẽ tràn khỏi lỗ vòng.
   */
  formatTotal?: (total: number) => string
  /** Định dạng số trong chú giải. Mặc định giống `formatTotal`. */
  formatValue?: (value: number) => string
}

/**
 * Vòng khuyên tỉ trọng — chỉ dùng khi cần thấy "phần trên tổng" ở mức liếc mắt và
 * có tối đa ~6 lát. So sánh các giá trị sát nhau thì dùng cột ngang.
 *
 * Chú giải bên dưới ghi rõ số và tỉ lệ của từng lát nên không giá trị nào phải
 * rê chuột mới đọc được.
 */
export function DonutChart({
  data,
  centerLabel,
  unit,
  formatTotal = (total) => total.toLocaleString('vi-VN'),
  formatValue,
}: DonutChartProps) {
  const total = data.reduce((sum, slice) => sum + slice.value, 0)
  const formatLegend = formatValue ?? formatTotal

  return (
    <div className="space-y-4">
      <div className="relative">
        <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="label"
              cx="50%"
              cy="50%"
              innerRadius={52}
              outerRadius={80}
              // Viền màu nền = khe hở 2px tách hai lát, không phải nét kẻ trang trí.
              stroke="var(--card)"
              strokeWidth={2}
              isAnimationActive={false}
            >
              {data.map((slice) => (
                <Cell key={slice.label} fill={slice.color} />
              ))}
            </Pie>
            <Tooltip
              wrapperStyle={{ outline: 'none' }}
              content={<ChartTooltipContent unit={unit} />}
            />
          </PieChart>
        </ResponsiveContainer>

        {/* Tổng đặt giữa vòng. `pointer-events-none` để không chắn vùng rê chuột. */}
        {/* `max-w` bằng đường kính lỗ vòng: số dài quá thì xuống dòng/cắt bên
            trong lỗ chứ không tràn đè lên các lát bánh. */}
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="max-w-[96px] truncate text-center text-xl font-semibold text-navy dark:text-foreground">
            {formatTotal(total)}
          </span>
          <span className="text-xs text-muted-foreground">{centerLabel}</span>
        </div>
      </div>

      <ul className="space-y-2">
        {data.map((slice) => (
          <ChartLegendItem
            key={slice.label}
            color={slice.color}
            label={slice.label}
            value={formatLegend(slice.value)}
            hint={total > 0 ? `${Math.round((slice.value / total) * 100)}%` : '0%'}
          />
        ))}
      </ul>
    </div>
  )
}
