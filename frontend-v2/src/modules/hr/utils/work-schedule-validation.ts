import { WORK_DAY_KIND_CODE } from '../types/work-schedule'
import { WEEKDAY_LABELS, fillWeek } from './work-schedule-week'

/** Cấp, mẫu lịch: id phải là số dương (0 / rỗng / NaN = chưa chọn). */
export function isChosenId(value: unknown): boolean {
  const id = Number(value)
  return Number.isInteger(id) && id > 0
}

/**
 * Kiểm bảy ngày TRƯỚC khi gửi: ngày đi làm phải có giờ vào và giờ ra, giờ ra sau
 * giờ vào, giờ nghỉ trưa khai đủ cặp. Trả câu tiếng Việt nêu đúng thứ sai, hoặc
 * `true`. Luật sâu hơn (trưa nằm gọn trong khung…) vẫn do backend giữ; chỗ này chỉ
 * để người dùng không nhận khóa lỗi thô ở toast. Dữ liệu thiếu thứ được `fillWeek`
 * bù thành «Nghỉ» nên luôn đủ bảy hàng.
 */
export function validateWeekDays(days: unknown): string | true {
  for (const day of fillWeek(days)) {
    const label = WEEKDAY_LABELS[day.weekday]
    if (day.day_kind === WORK_DAY_KIND_CODE.OFF) continue
    if (!day.start_time || !day.end_time) return `${label}: nhập đủ giờ vào và giờ ra.`
    if (day.end_time <= day.start_time) return `${label}: giờ ra phải sau giờ vào.`
    if (day.day_kind === WORK_DAY_KIND_CODE.FULL && Boolean(day.lunch_start) !== Boolean(day.lunch_end)) {
      return `${label}: nhập đủ cả giờ nghỉ trưa từ và đến, hoặc để trống cả hai.`
    }
  }
  return true
}
