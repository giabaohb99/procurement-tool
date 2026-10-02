import { ChartCard } from '@/shared/ui/chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'

import type {
  ReportBreakdownConfig,
  ReportBreakdownItem,
  ReportMeta,
} from '../types/report-analytics'
import { describeBreakdownRank } from '../utils/breakdown-rank-metric'

interface ReportBreakdownChartsProps {
  breakdowns?: Record<string, ReportBreakdownItem[]>
  config: ReportBreakdownConfig[]
  /** Khối Top xếp theo chỉ số nào — `meta.rank_by` mặc định, từng thẻ ghi đè bằng `ReportBreakdownConfig.rankMetric`. */
  meta?: ReportMeta
  isLoading: boolean
}

/**
 * Biểu đồ "Top" phụ (Top NCC, Top NSTM…) — CHỈ vẽ những khóa trang đã khai
 * trong `ReportPageConfig.breakdowns`; backend không trả khóa nào trong
 * `response.breakdowns` thì thẻ đó hiện rỗng chứ không tự ẩn (đúng ý người
 * cấu hình: đã khai là muốn có chỗ cho nó, kể cả lúc chưa có dữ liệu).
 */
export function ReportBreakdownCharts({
  breakdowns,
  config,
  meta,
  isLoading,
}: ReportBreakdownChartsProps) {
  if (config.length === 0) return null

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {config.map((c) => {
        const items = breakdowns?.[c.key] ?? []
        //  H3 (review 01/10/2026) — mỗi thẻ tự tính phụ đề/định dạng theo ĐÚNG
        //  chỉ số của NÓ (`c.rankMetric`), không dùng chung `meta.rank_by`:
        //  trang nhiều breakdown xếp theo nhiều chỉ số khác nhau (vd dự án) thì
        //  một mô tả chung cho mọi thẻ sẽ sai với ít nhất một thẻ.
        const { description, formatValue } = describeBreakdownRank(meta, c.rankMetric)
        return (
          <ChartCard
            key={c.key}
            title={c.title}
            description={description}
            loading={isLoading}
            isEmpty={items.length === 0}
          >
            <HorizontalBarChart
              data={items.map((item) => ({ label: item.label, value: item.value }))}
              formatValue={formatValue}
            />
          </ChartCard>
        )
      })}
    </div>
  )
}
