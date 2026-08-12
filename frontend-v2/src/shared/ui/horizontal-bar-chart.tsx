import { Bar, BarChart, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { ChartTooltipContent, type ChartDatum } from './chart'

/** Chiều cao một dòng (cột + khoảng thở). Quyết định chiều cao cả biểu đồ. */
const ROW_HEIGHT = 40
/** Cột không bao giờ dày hơn ngần này — phần dư của dòng để làm khoảng trống. */
const MAX_BAR_SIZE = 20
/** Nhãn trục Y dài hơn thì cắt bớt; tên đầy đủ vẫn xem được ở tooltip. */
const MAX_TICK_CHARS = 26

interface HorizontalBarChartProps {
  data: ChartDatum[]
  /** Đơn vị hiện trong tooltip, vd "nhân sự". */
  unit?: string
  /** Màu cột. Một chuỗi dữ liệu = MỘT màu cho mọi cột. */
  color?: string
}

/**
 * Cột ngang so sánh độ lớn giữa các hạng mục (phòng ban, pháp nhân…).
 *
 * Chỉ MỘT màu cho tất cả các cột: chiều dài cột đã nói lên độ lớn rồi, tô đậm
 * nhạt theo giá trị là mã hóa hai lần cùng một thông tin và đốt mất kênh màu.
 * Cũng vì vậy không cần chú giải — tiêu đề thẻ đã nói biểu đồ đếm cái gì.
 */
export function HorizontalBarChart({
  data,
  unit,
  color = 'var(--chart-1)',
}: HorizontalBarChartProps) {
  return (
    // Chiều cao cố định theo số dòng (đủ chỗ mọi cột, không sinh thanh cuộn con);
    // thẻ cao hơn thì biểu đồ nằm GIỮA phần dư chứ không giãn các dòng ra xa nhau.
    <div className="flex flex-1 items-center">
      <ResponsiveContainer width="100%" height={data.length * ROW_HEIGHT + 8}>
        <BarChart
          data={data}
          layout="vertical"
          // Chừa lề phải cho nhãn số ở đầu cột khỏi bị cắt.
          margin={{ top: 4, right: 36, bottom: 4, left: 0 }}
          barCategoryGap={8}
        >
          {/* Trục X ẩn: mọi cột đã có số ghi thẳng ở đầu, thêm lưới chỉ tổ rối. */}
          <XAxis type="number" hide domain={[0, 'dataMax']} />
          <YAxis
            type="category"
            dataKey="label"
            width="auto"
            tickLine={false}
            axisLine={false}
            tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
            tickFormatter={(value: string) =>
              value.length > MAX_TICK_CHARS ? `${value.slice(0, MAX_TICK_CHARS - 1)}…` : value
            }
          />
          <Tooltip
            cursor={{ fill: 'var(--accent)' }}
            wrapperStyle={{ outline: 'none' }}
            content={<ChartTooltipContent unit={unit} />}
          />
          <Bar
            dataKey="value"
            fill={color}
            // Bo 4px ở ĐẦU cột, vuông ở chân cột (chỗ bám vạch gốc).
            radius={[0, 4, 4, 0]}
            maxBarSize={MAX_BAR_SIZE}
          >
            <LabelList
              dataKey="value"
              position="right"
              offset={8}
              fill="var(--foreground)"
              fontSize={12}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
