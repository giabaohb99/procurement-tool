import { apiGet } from '@/core/api'
import type {
  AssignableEmployeePage,
  EffectiveDepartmentWorkSchedule,
  EffectiveWorkSchedule,
} from '../types/work-schedule'
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
   * Lịch ĐANG ÁP cho một phòng ban tại `onDate` (mặc định hôm nay giờ VN ở backend), kèm các
   * dòng gán cấp phòng ban của phòng đó. Gác `department.read` — cùng quyền mở trang phòng ban.
   */
  getEffectiveForDepartment: (departmentId: number, onDate?: string) =>
    apiGet<EffectiveDepartmentWorkSchedule>('/api/work-schedules/tools/effective-department', {
      params: { department_id: departmentId, on_date: onDate },
    }),
  /**
   * Lưới "ai làm, ai nghỉ" cho một khoảng ngày (tối đa 42 ngày), phân trang theo
   * nhân sự. Gác `employee.read` + phạm vi nhân sự; lớp nghỉ phép chỉ hiện ở ô
   * nào người xem đọc được đơn.
   */
  /**
   * Nhân sự ĐANG LÀM mà người gọi gán được lịch riêng (duoc-CR-757 lượt 2): Nhân sự → phạm vi đọc `employee`;
   * Trưởng phòng (`work_schedule_personal.create`) → đúng nhân viên trong phạm vi khóa đó, trừ chính mình; thiếu cả hai
   * khóa → 403. Sắp theo họ tên.
   */
  listAssignableEmployees: (params: { q?: string; page?: number; page_size?: number } = {}) =>
    apiGet<AssignableEmployeePage>('/api/work-schedule-assignments/tools/assignable-employees', { params }),
  getRoster: (params: WorkRosterParams) =>
    apiGet<WorkRoster>('/api/work-schedules/tools/roster', { params }),
}
