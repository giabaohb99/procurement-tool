import { apiGet } from '@/core/api'

import type { MonthlyReminders } from '../types/monthly-reminders'

/** Lịch nhắc của MỘT tháng (`YYYY-MM`) trong phạm vi người xem — duoc-CR-689. */
export function fetchMonthlyReminders(month: string) {
  return apiGet<MonthlyReminders>('/api/employees/monthly-reminders', { params: { month } })
}
