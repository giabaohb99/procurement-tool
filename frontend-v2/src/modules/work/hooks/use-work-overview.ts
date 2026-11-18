import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'

import { apiGet } from '@/core/api'
import { CHART_COLORS } from '@/shared/ui/chart'
import type { DonutSlice } from '@/shared/ui/donut-chart'
import { queryKeys } from '@/shared/constants/query-keys'

/**
 * Một dòng việc RÚT GỌN của màn Tổng quan — chỉ đủ để nhận ra và bấm vào.
 *
 * Không có mô tả, nhãn hay người phụ trách: đó là việc của thẻ chi tiết, kéo
 * thêm về đây là thêm hai lượt join cho một màn vốn thuần đếm.
 */
export interface WorkOverviewTask {
  id: number
  list_id: number
  list_name: string
  title: string
  /** `""` = chưa đặt hạn. */
  due_date: string
  /** Chỉ dòng QUÁ HẠN có (duoc-CR-782): số ngày trễ tính tới hôm nay. */
  overdue_days?: number
  /** Chỉ dòng QUÁ HẠN có (duoc-CR-782): tên người phụ trách. */
  assignees?: string[]
  /**
   * `false` = người xem KHÔNG là thành viên dự án chứa việc (phạm vi "mọi dự án") — mở ra là 403, nên giao diện không
   * dẫn link. Thiếu khóa (danh sách "Việc của tôi") = mở được.
   */
  can_open?: boolean
}

/** `scope` của màn Tổng quan: `all` = mọi dự án (được giao xem báo cáo Công việc & Dự án), `member` = dự án mình tham gia. */
export type WorkOverviewScope = 'all' | 'member'

/** Một dòng của bảng đối chiếu theo người (duoc-CR-782) — đúng khuôn `overview_people.people_rows`. */
export interface WorkOverviewPerson {
  employee_id: number
  name: string
  code: string
  avatar: string
  open: number
  overdue: number
  /** Đến hạn trong 7 ngày tới (tính cả hôm nay), chưa quá hạn. */
  due_soon: number
  done_in_period: number
  /** % xong đúng hạn trong kỳ; `null` = chưa có việc xong nào có hạn để đo. */
  on_time_rate: number | null
  /** Việc quá hạn lâu nhất đã trễ bao nhiêu ngày; 0 = không có việc quá hạn. */
  max_overdue_days: number
  estimate_hours_open: number
  actual_hours_done: number
  /** Lần cập nhật gần nhất trên việc người này phụ trách (ISO, giờ máy chủ UTC) — `null` = chưa có. */
  last_update: string | null
}

/** Mã sức khỏe dự án — khớp `overview_projects.ProjectHealth` (giá trị suy ra, backend trả kèm nhãn). */
export const PROJECT_HEALTH = { NO_TASKS: 0, ON_TRACK: 1, AT_RISK: 2, LATE: 3 } as const

/** Một dòng sức khỏe dự án (duoc-CR-782) — đúng khuôn `overview_projects.project_rows`. */
export interface WorkOverviewProject {
  list_id: number
  name: string
  color: string
  total: number
  done: number
  open: number
  overdue: number
  /** Việc xong trong kỳ đang chọn (đường trên biểu đồ dự án). */
  done_in_period: number
  /** % hoàn thành (việc hủy không vào mẫu số). */
  progress: number
  /** Hạn xa nhất trong số việc còn mở; `""` = không việc mở nào có hạn. */
  last_due: string
  health: number
  health_label: string
  /** `false` = không là thành viên dự án này — xem số được, mở bảng việc thì không. */
  can_open: boolean
}

/** Một việc trong hộp "việc của một người" (duoc-CR-782). */
export interface WorkOverviewPersonTask {
  id: number
  list_id: number
  list_name: string
  title: string
  due_date: string
  overdue: boolean
  /** `false` = không là thành viên dự án chứa việc — không dẫn link. */
  can_open: boolean
}

/** Đúng khuôn `overview_service.overview` bên backend. */
export interface WorkOverview {
  scope: WorkOverviewScope
  period_days: number
  project_total: number
  project_archived: number
  task_open: number
  task_done: number
  task_cancelled: number
  task_overdue: number
  task_mine: number
  /** Đang mở, đến hạn trong 7 ngày tới (tính cả hôm nay), chưa quá hạn. */
  task_due_soon: number
  task_created_in_period: number
  task_done_in_period: number
  /** % xong đúng hạn trong kỳ; `null` = chưa có việc nào để đo (không phải 0%). */
  on_time_rate: number | null
  /** Việc đang mở chưa có người phụ trách. */
  task_unassigned: number
  /** Việc đang mở chưa đặt hạn. */
  task_no_due: number
  by_project: { list_id: number; name: string; open: number }[]
  /**
   * Đếm theo BẬC ƯU TIÊN, gộp chung mọi dự án theo TÊN bậc — độ ưu tiên nay là
   * một trường tùy biến của từng dự án nên không còn mã số chung nào để gộp.
   */
  by_priority: { name: string; color: string; open: number }[]
  /** Tối đa 8 việc quá hạn, hạn CŨ NHẤT trước. */
  overdue_tasks: WorkOverviewTask[]
  /** Tối đa 8 việc tôi phụ trách, hạn gần nhất trước; chưa đặt hạn xuống cuối. */
  my_tasks: WorkOverviewTask[]
  /** Tối đa 8 việc chưa ai nhận, hạn gần nhất trước. */
  unassigned_tasks: WorkOverviewTask[]
  /** Tối đa 8 việc chưa đặt hạn, việc tạo lâu nhất trước. */
  no_due_tasks: WorkOverviewTask[]
  /** Bảng theo người — người nhiều việc quá hạn lên đầu. */
  people: WorkOverviewPerson[]
  /** Sức khỏe dự án chưa lưu trữ — dự án trễ lên đầu. */
  projects: WorkOverviewProject[]
}

/** Kỳ chọn được cho các chỉ số "trong kỳ" của màn Tổng quan. */
export const WORK_OVERVIEW_PERIODS = [7, 30, 90] as const
export const DEFAULT_WORK_OVERVIEW_PERIOD = 30

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
export function useWorkOverview(periodDays: number = DEFAULT_WORK_OVERVIEW_PERIOD, listId?: number) {
  const query = useQuery({
    queryKey: queryKeys.work.overview(periodDays, listId),
    //  `list_id` = báo cáo riêng một dự án (tab Báo cáo trong chi tiết dự án).
    queryFn: () =>
      apiGet<WorkOverview>('/api/work/overview', { params: { period_days: periodDays, list_id: listId } }),
    //  Đổi kỳ không làm cả trang nháy về khung xương: giữ số cũ tới khi số mới về.
    placeholderData: keepPreviousData,
  })

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

  return { ...query, byPriority }
}

/** Việc đang mở của một người phụ trách — chỉ gọi khi hộp chi tiết của người đó đang mở. */
export function useWorkOverviewPersonTasks(employeeId: number | null) {
  return useQuery({
    queryKey: queryKeys.work.overviewPersonTasks(employeeId ?? 0),
    queryFn: () =>
      apiGet<WorkOverviewPersonTask[]>(`/api/work/overview/people/${employeeId}/tasks`),
    enabled: employeeId !== null,
  })
}

/** Đối tượng của khối theo dõi diễn biến: một dự án hoặc một người phụ trách. */
export type WorkOverviewTrendKind = 'project' | 'person'

/** Một mốc (ngày hoặc tuần) của chuỗi diễn biến — đúng khuôn `overview_trend.trend`. */
export interface WorkOverviewTrendBucket {
  /** Ngày bắt đầu mốc, `YYYY-MM-DD`. */
  start: string
  /** Nhãn trục, `dd/MM` (mốc tuần = ngày đầu tuần). */
  label: string
  /** Việc mới giao (tạo) trong mốc. */
  created: number
  done_on_time: number
  done_late: number
  done_no_due: number
}

export interface WorkOverviewTrend {
  granularity: 'day' | 'week'
  /** Rỗng khi đối tượng nằm ngoài phạm vi xem. */
  buckets: WorkOverviewTrendBucket[]
}

/** Diễn biến của một dự án / một người — chỉ gọi khi đã chọn đối tượng. */
export function useWorkOverviewTrend(kind: WorkOverviewTrendKind, id: number | null, periodDays: number) {
  return useQuery({
    queryKey: queryKeys.work.overviewTrend(kind, id ?? 0, periodDays),
    queryFn: () =>
      apiGet<WorkOverviewTrend>('/api/work/overview/trend', {
        params: { kind, id, period_days: periodDays },
      }),
    enabled: id !== null,
    placeholderData: keepPreviousData,
  })
}
