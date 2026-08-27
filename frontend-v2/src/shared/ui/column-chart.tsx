import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { ChartTooltipContent, type ChartDatum } from './chart'

interface ColumnChartProps {
  data: ChartDatum[]
  height?: number
  /** Đơn vị trong tooltip, vd "đ". */
  unit?: string
  /** Rút gọn số trên trục Y và trong tooltip (vd 286.000.000 -> "286 tr"). */
  formatValue?: (value: number) => string
  color?: string
  /**
   * Bấm vào một cột — nhận CHỈ SỐ của cột trong `data` (chỗ gọi tự tra lại mốc
   * thời gian tương ứng). Bỏ trống = biểu đồ chỉ để xem, con trỏ giữ nguyên.
   */
  onBarClick?: (index: number) => void
}

/**
 * Biểu đồ CỘT DỌC theo thời gian (12 tháng, 4 quý…). Trục X là mốc thời gian
 * nên phải giữ đủ mọi mốc kể cả tháng chưa phát sinh — cột 0 cũng là thông tin.
 *
 * Khác `HorizontalBarChart` (so sánh giữa các hạng mục, nhãn dài, sắp theo độ
 * lớn): ở đây thứ tự cột là thứ tự thời gian, không được sắp lại.
 */
export function ColumnChart({
  data,
  height = 280,
  unit,
  formatValue,
  color = 'var(--chart-1)',
  onBarClick,
}: ColumnChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        {/* Chỉ kẻ ngang: vạch dọc giữa các tháng không giúp đọc giá trị. */}
        <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
        <XAxis
          dataKey="label"
          tickLine={false}
          axisLine={false}
          tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
        />
        <YAxis
          width="auto"
          tickLine={false}
          axisLine={false}
          tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
          tickFormatter={(value: number) => formatValue?.(value) ?? String(value)}
        />
        <Tooltip
          cursor={{
            //  Dải sáng sau cột đang rê chuột. Dùng CHUNG token với hàng bảng
            //  danh sách để cả ứng dụng chỉ có một thứ tiếng "chỗ này đang được
            //  trỏ tới".
            //
            //  ⚠️ TRƯỚC ĐÂY là `var(--accent)` và hỏng ở bảng màu nhập ngoài:
            //  `accent` của shadcn là màu NHẤN cho nút/mục menu nhỏ, nhiều bảng
            //  màu đặt nó đậm hẳn (Starry Night #6ea3c1 xanh thép) — tô đục cả
            //  một dải ngang sau cột thì cột chìm vào chính cái dải đó. Lỗi
            //  thấy được 27/08/2026.
            fill: 'var(--row-hover)',
          }}
          wrapperStyle={{ outline: 'none' }}
          content={<ChartTooltipContent unit={unit} formatValue={formatValue} />}
        />
        <Bar
          dataKey="value"
          fill={color}
          radius={[4, 4, 0, 0]}
          maxBarSize={36}
          // Đối số đầu là hình chữ nhật recharts vẽ ra, không phải mục dữ liệu
          // gốc — nên trả CHỈ SỐ về cho chỗ gọi tự tra trong `data`.
          onClick={onBarClick ? (_bar, index) => onBarClick(index) : undefined}
          className={onBarClick ? 'cursor-pointer' : undefined}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
