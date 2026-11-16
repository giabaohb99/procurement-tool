/**
 * Kiểu dữ liệu của XẾP CA THEO NGÀY (duoc-CR-761) — khớp `/api/work-shifts` ở
 * `backend/app/modules/work_schedule/shift_controller.py`.
 *
 * Khung giờ là giờ TRÒN, bán mở `[start_hour, end_hour)`: 0 ≤ start < end ≤ 24 (24 = hết ngày).
 * Ngày có ca mà không khung nào = NGHỈ do xếp ca. Ngày không có ca = theo mẫu lịch tuần.
 */

import type { WorkRosterItem } from './work-roster'

/** Ô (người × ngày) đang mở hộp xếp ca trên lưới Xem lịch. */
export interface WorkShiftTarget {
  item: WorkRosterItem
  date: string
}

/** Một khung giờ dạng cặp `[giờ đầu, giờ cuối)`. */
export type HourRange = readonly [start: number, end: number]

export interface WorkShiftSegment {
  start_hour: number
  end_hour: number
  /** "08:00–10:00" (giờ cuối 24 hiện "24:00"). */
  label: string
}

/** Một ngày đã xếp ca (API quản lý). */
export interface WorkShift {
  id: number
  employee_id: number
  work_date: string
  note: string
  segments: WorkShiftSegment[]
  hours: number
  is_day_off: boolean
}

/** Một ngày trong "Ca của tôi" (`/api/work-shifts/me`) — mẫu tuần và ca xếp riêng đã gộp. */
export interface MyShiftDay {
  date: string
  /** 0 = Thứ Hai … 6 = Chủ nhật. */
  weekday: number
  /** `true` = ngày này có ca xếp riêng (thắng mẫu tuần). */
  is_shift: boolean
  work_kind: number
  work_kind_label: string
  start_time: string | null
  end_time: string | null
  /** Nhãn khung "08:00–12:00"; mẫu tuần tách quanh giờ nghỉ trưa. Rỗng = không phải đi làm. */
  segments: string[]
  /** Chỉ ngày xếp ca. */
  ranges: number[][]
  hours: number
  note: string
  /** Không phải đi làm (CN / nghỉ do xếp ca / mẫu nghỉ). KHÔNG tính ngày lễ. */
  is_day_off: boolean
  is_holiday: boolean
  holiday_name: string
  schedule_name: string
}

export interface MyShiftRange {
  /** `0` = tài khoản chưa gắn hồ sơ nhân sự (khi đó `days` rỗng). */
  employee_id: number
  from_date: string
  to_date: string
  days: MyShiftDay[]
}

/** Thân `PUT /{employee_id}/{work_date}` và phần chung của `/bulk`. Danh sách rỗng = nghỉ cả ngày. */
export interface WorkShiftBody {
  segments: { start_hour: number; end_hour: number }[]
  note: string
}

export interface WorkShiftBulkBody extends WorkShiftBody {
  employee_ids: number[]
  dates: string[]
}

export interface WorkShiftBulkResult {
  created: number
  updated: number
  changed: number
}

export interface WorkShiftCopyWeekBody {
  employee_ids: number[]
  /** Thứ Hai `YYYY-MM-DD`. */
  source_week_start: string
  target_week_start: string
  overwrite: boolean
}

export interface WorkShiftCopyWeekResult extends WorkShiftBulkResult {
  skipped: number
  /** Đường Trưởng phòng: số ngày đích đã qua bị bỏ qua (không từ chối cả lượt). */
  skipped_past: number
  /** Ngày đích đã có đơn nghỉ (chờ duyệt / đã duyệt) nên không chép. Vắng = backend trước luật này. */
  skipped_leave?: number
  /** Từng ngày bị bỏ qua vì đơn nghỉ; `request_code` rỗng khi người xem không được xem đơn đó. */
  leave_conflicts?: { employee_id: number; work_date: string; request_code: string }[]
}

/** Một ô bị từ chối trong lượt ghi hàng loạt (`error.details.rejected`, mã lỗi `shift_rejected`). */
export interface WorkShiftRejection {
  employee_id: number
  /** `null` = cả nhân sự (ngoài phạm vi / không tồn tại / chính mình). */
  work_date: string | null
  code: 'not_found' | 'self' | 'past_date' | 'leave_conflict' | string
  message: string
}
