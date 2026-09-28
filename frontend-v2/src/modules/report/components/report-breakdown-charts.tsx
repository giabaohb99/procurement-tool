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
  /** Để biết khối Top xếp theo chỉ số nào (`meta.rank_by`) và định dạng số theo nó. */
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
  const { description, formatValue } = describeBreakdownRank(meta)

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {config.map((c) => {
        const items = breakdowns?.[c.key] ?? []
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
