import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { fetchMonthlyReminders } from '../api/monthly-reminders-api'

/**
 * Lịch nhắc trong tháng (duoc-CR-689). `enabled` = có `employee.read` — thiếu mà vẫn gọi thì
 * người mở Tổng quan Nhân sự ăn 403 ngay. Giữ số tháng trước khi đang tải tháng mới để ô không
 * chớp trắng mỗi lần bấm mũi tên.
 */
export function useMonthlyReminders(month: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.monthlyReminders(month),
    queryFn: () => fetchMonthlyReminders(month),
    enabled,
    placeholderData: keepPreviousData,
  })
}
