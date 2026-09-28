import { ChartCard } from '@/shared/ui/chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'

import type { ReportAnalyticsResponse } from '../types/report-analytics'
import { describeBreakdownRank } from '../utils/breakdown-rank-metric'

interface ReportOverviewTopListsProps {
  /** Response CỦA Báo cáo mua hàng (đã gọi sẵn cho dải KPI) — không gọi thêm API. */
  data?: ReportAnalyticsResponse
  isLoading: boolean
}

/** Chiều không nhạy cảm, luôn có mặt trong `breakdowns` — hiện khung xương ngay cả khi chưa có `data`. */
const ALWAYS_KEYS = ['department', 'item_group'] as const
/** Chiều nhạy cảm (NCC/NSPT) — chỉ hiện khi backend THẬT SỰ trả khóa đó (`_can_see_ncc`). */
const CONDITIONAL_KEYS = ['supplier', 'nspt'] as const

const TITLES: Record<string, string> = {
  department: 'Top bộ phận',
  item_group: 'Top nhóm hàng',
  supplier: 'Top NCC',
  nspt: 'Top NSPT',
}

/**
 * "Top lists" của trang Tổng quan — lấy thẳng từ `breakdowns` của Báo cáo mua
 * hàng, KHÔNG gọi thêm API (`aggregate()` ở backend luôn tính đủ `breakdowns`
 * dù gọi `group_by=none`). NCC/NSPT chỉ hiện khi khóa đó THẬT SỰ có mặt trong
 * response — không suy đoán bằng `can()` ở tầng frontend, vì đây là quyền của
 * phân hệ khác (`purchase_order.read`), không phải quyền đọc báo cáo.
 */
export function ReportOverviewTopLists({ data, isLoading }: ReportOverviewTopListsProps) {
  const conditionalKeys = CONDITIONAL_KEYS.filter((key) => data?.breakdowns?.[key] !== undefined)
  const keys = [...ALWAYS_KEYS, ...conditionalKeys]
  const { description, formatValue } = describeBreakdownRank(data?.meta)

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {keys.map((key) => {
        const items = data?.breakdowns?.[key] ?? []
        return (
          <ChartCard
            key={key}
            title={TITLES[key]}
            description={description}
            loading={isLoading}
            isEmpty={items.length === 0}
            emptyLabel="Kỳ này chưa có dữ liệu."
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
