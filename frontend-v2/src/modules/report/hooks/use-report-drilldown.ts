import { useQuery } from '@tanstack/react-query'

import { reportDrilldownApi } from '../api/report-drilldown-api'

/**
 * Khóa CỤC BỘ (ngoại lệ đã ghi ở `.claude/rules/naming.md`): chỉ hook này dùng, không nơi nào
 * vô hiệu hóa riêng nó. Đầu khóa vẫn là `'report'` nên vô hiệu hóa cả phân hệ Báo cáo vẫn trúng.
 */
const drilldownKeys = {
  rows: (endpoint: string, params: Record<string, string>) =>
    ['report', 'drilldown', endpoint, params] as const,
}

/**
 * Danh sách người của ngăn «Xem danh sách» (duoc-CR-686). `params = null` (ngăn đang đóng)
 * thì KHÔNG gọi — mở trang báo cáo không tốn lượt `/rows` nào.
 *
 * Không `keepPreviousData`: đổi chỉ số là đổi cả bộ cột (vd «Chưa được cấp quỹ» có cột
 * khác hẳn dòng quỹ) — giữ bảng cũ tới khi bảng mới về là vẽ dữ liệu mới lên cột cũ.
 */
export function useReportDrilldown(endpoint: string | undefined, params: Record<string, string> | null) {
  return useQuery({
    queryKey: drilldownKeys.rows(endpoint ?? '', params ?? {}),
    queryFn: () => reportDrilldownApi.get(endpoint as string, params as Record<string, string>),
    enabled: !!endpoint && params !== null,
  })
}
