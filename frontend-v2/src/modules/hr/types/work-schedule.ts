/**
 * Kiểu dữ liệu của «Lịch làm việc» — khớp hợp đồng API ở
 * `plans/261005-0925-hr-lich-lam-viec/phase-02-*.md` §API.
 *
 * NHÃN và danh sách chọn lấy từ `@/shared/constants/statuses` (`WORK_DAY_KIND`,
 * `WORK_SCHEDULE_LEVEL`, do `gen_status_ts.py` sinh). Hằng `*_CODE` bên dưới chỉ
 * để rẽ nhánh logic bằng tên thay vì số trần; test chốt chúng khớp bộ mã sinh.
 */

import { WORK_SCHEDULE_LEVEL } from '@/shared/constants/statuses'

/** Loại ngày làm việc (`WorkDayKind` backend). */
export const WORK_DAY_KIND_CODE = { OFF: 1, FULL: 2, MORNING: 3, AFTERNOON: 4 } as const

/** Cấp gán lịch (`WorkScheduleLevel` backend). */
export const WORK_SCHEDULE_LEVEL_CODE = { SYSTEM: 1, COMPANY: 2, DEPARTMENT: 3, EMPLOYEE: 4 } as const

/** Nhãn cấp «Toàn hệ thống» lấy từ bộ mã sinh — mọi chỗ hiển thị dùng đúng một nhãn này. */
export const SYSTEM_LEVEL_LABEL =
  WORK_SCHEDULE_LEVEL.find((o) => Number(o.value) === WORK_SCHEDULE_LEVEL_CODE.SYSTEM)?.label ??
  'Toàn hệ thống'

/** Một ngày trong tuần của mẫu lịch. `weekday` 0 = Thứ Hai … 6 = Chủ nhật; giờ dạng "HH:MM" hoặc null. */
export interface WorkScheduleDay {
  weekday: number
  day_kind: number
  start_time: string | null
  end_time: string | null
  lunch_start: string | null
  lunch_end: string | null
}

//  ⚠️ `type`, KHÔNG `interface`: khung CRUD ràng `T extends CrudRecord`, mà chỉ type alias
//  mới có chỉ mục ngầm — cùng lý do với `LeaveType` / `JobPosition`.
export type WorkSchedule = {
  id: number
  name: string
  note: string
  is_active: boolean
  days: WorkScheduleDay[]
  weekly_workdays: number
  assignment_count: number
  created_at?: string
  updated_at?: string
}

export type WorkScheduleAssignment = {
  id: number
  target_level: number
  target_level_label: string
  /** `0` ở cấp «Toàn hệ thống». */
  target_id: number
  target_name: string
  schedule_id: number
  schedule_name: string
  effective_from: string
  effective_to: string | null
  note: string
  is_current: boolean
}

/** Lịch đang áp cho một nhân sự (`/api/work-schedules/tools/effective`). */
export interface EffectiveWorkSchedule {
  /** `0` khi dùng lịch mặc định trong mã (chưa ai gán). */
  schedule_id: number
  schedule_name: string
  days: WorkScheduleDay[]
  weekly_workdays: number
  is_fallback: boolean
  /** `0` khi `is_fallback`. */
  level: number
  level_label?: string
  target_name?: string
  assignment_id?: number
  effective_from?: string | null
  effective_to?: string | null
}
