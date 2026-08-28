import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import { apiGet } from '@/core/api'
import { CHART_COLORS, type ChartDatum } from '@/shared/ui/chart'
import type { DonutSlice } from '@/shared/ui/donut-chart'
import { queryKeys } from '@/shared/constants/query-keys'
import { WORK_PRIORITY, WORK_PRIORITY_LABELS } from '../types/work'

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
  by_priority: { priority: number; open: number }[]
}

/**
 * Số liệu màn Tổng quan phân hệ Dự án.
 *
 * Khác Tổng quan Nhân sự (gom ở trình duyệt): việc nằm rải trong từng dự án và
 * API bảng lấy theo TỪNG dự án, gom ở client là hàng chục lượt gọi. Nên đếm ở
 * máy chủ, ở đây chỉ dịch số sang nhãn để vẽ.
 *
 * Nhãn mức ưu tiên dịch TẠI ĐÂY chứ không để backend trả chữ — đúng luật R2:
 * cột trạng thái/mức độ lưu số, tiếng Việt chỉ sống ở tầng hiển thị.
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
        .map((row) => ({
          label:
            WORK_PRIORITY_LABELS[row.priority] ??
            WORK_PRIORITY_LABELS[WORK_PRIORITY.NONE],
          value: row.open,
          //  Màu gán theo CHÍNH MỨC ƯU TIÊN, không theo thứ hạng trong mảng:
          //  lọc bớt một mức mà màu các mức còn lại đổi theo thì người đã quen
          //  "P1 màu này" sẽ đọc nhầm (ghi chú ở `chart.tsx`).
          color: CHART_COLORS[row.priority % CHART_COLORS.length],
        })),
    [query.data],
  )

  return { ...query, byProject, byPriority }
}
