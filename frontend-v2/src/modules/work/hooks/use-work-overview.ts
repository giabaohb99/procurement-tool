import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import { apiGet } from '@/core/api'
import { CHART_COLORS, type ChartDatum } from '@/shared/ui/chart'
import type { DonutSlice } from '@/shared/ui/donut-chart'
import { queryKeys } from '@/shared/constants/query-keys'

/** Đúng khuôn `overview_service.overview` bên backend. */
export interface WorkOverview {
  project_total: number
  project_archived: number
  task_open: number
  task_done: number
  task_cancelled: number
  task_overdue: number
  task_mine: number
  by_project: { list_id: number; name: string; open: number }[]
  /**
   * Đếm theo BẬC ƯU TIÊN, gộp chung mọi dự án theo TÊN bậc — độ ưu tiên nay là
   * một trường tùy biến của từng dự án nên không còn mã số chung nào để gộp.
   */
  by_priority: { name: string; color: string; open: number }[]
}

/**
 * Số liệu màn Tổng quan phân hệ Dự án.
 *
 * Khác Tổng quan Nhân sự (gom ở trình duyệt): việc nằm rải trong từng dự án và
 * API bảng lấy theo TỪNG dự án, gom ở client là hàng chục lượt gọi. Nên đếm ở
 * máy chủ, ở đây chỉ dịch số sang nhãn để vẽ.
 *
 * Tên bậc ưu tiên do BACKEND trả (không dịch ở đây nữa): từ khi độ ưu tiên
 * thành trường tùy biến, tên bậc là dữ liệu người dùng tự đặt cho từng dự án.
 */
export function useWorkOverview() {
  const query = useQuery({
    queryKey: queryKeys.work.overview(),
    queryFn: () => apiGet<WorkOverview>('/api/work/overview'),
  })

  const byProject = useMemo<ChartDatum[]>(
    () =>
      (query.data?.by_project ?? [])
        //  Dự án chưa có việc nào thì bỏ khỏi biểu đồ: một cột dài 0 chỉ tổ
        //  chiếm chỗ của dự án đang thật sự chạy.
        .filter((row) => row.open > 0)
        .map((row) => ({ label: row.name, value: row.open })),
    [query.data],
  )

  const byPriority = useMemo<DonutSlice[]>(
    () =>
      (query.data?.by_priority ?? [])
        .filter((row) => row.open > 0)
        .map((row, i) => ({
          label: row.name,
          value: row.open,
          //  Backend đã xếp theo THỨ TỰ BẬC (P1 trước P4) nên màu gán theo chỉ
          //  số cũng là gán theo bậc — cùng ý với ghi chú ở `chart.tsx`.
          color: CHART_COLORS[i % CHART_COLORS.length],
        })),
    [query.data],
  )

  return { ...query, byProject, byPriority }
}
