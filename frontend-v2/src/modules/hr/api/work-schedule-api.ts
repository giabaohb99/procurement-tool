import { apiGet } from '@/core/api'
import type { EffectiveWorkSchedule } from '../types/work-schedule'
import type { WorkRoster, WorkRosterParams } from '../types/work-roster'

/**
 * Lịch làm việc của một nhân sự (đọc). Việc quản lý mẫu / gán lịch đi qua khung
 * CRUD chung (`config/work-schedule-*-crud.tsx`), không có hàm ở đây.
 */
export const workScheduleApi = {
  /**
   * Lịch ĐANG ÁP cho nhân sự tại `onDate` (mặc định hôm nay ở backend). Gác bằng
   * `employee.read` + phạm vi nhân sự: 404 khi hồ sơ nằm ngoài phạm vi người xem.
   */
  getEffective: (employeeId: number, onDate?: string) =>
    apiGet<EffectiveWorkSchedule>('/api/work-schedules/tools/effective', {
      params: { employee_id: employeeId, on_date: onDate },
    }),
  /**
   * Lưới «ai làm, ai nghỉ» cho một khoảng ngày (tối đa 42 ngày), phân trang theo
   * nhân sự. Gác `employee.read` + phạm vi nhân sự; lớp nghỉ phép chỉ hiện ở ô
   * nào người xem đọc được đơn.
   */
  getRoster: (params: WorkRosterParams) =>
    apiGet<WorkRoster>('/api/work-schedules/tools/roster', { params }),
}
