import type { MyShiftDay } from '../types/work-shift'
import { formatShiftHours } from './work-roster-cell'

/**
 * Đọc MỘT ngày của "Ca của tôi" (`/api/work-shifts/me`) thành dòng hiển thị ở Trang cá nhân (duoc-CR-761). Thuần.
 *
 * Thứ tự: ngày lễ → nghỉ do xếp ca → nghỉ theo lịch → ca xếp riêng → giờ theo mẫu tuần. Lễ đứng đầu vì công ty nghỉ
 * lễ; nếu ngày lễ vẫn có ca xếp riêng thì kèm chữ ca để người đó biết mình có ca.
 */
export type MyShiftTone = 'holiday' | 'shift-off' | 'off' | 'shift' | 'work'

export interface MyShiftDayView {
  tone: MyShiftTone
  /** Chữ chính: các khung giờ ("08:00–12:00 · 13:00–17:00") hoặc "Nghỉ" / tên ngày lễ. */
  text: string
  /**
   * Cùng nội dung nhưng tách từng mảnh để thẻ hẹp XUỐNG DÒNG giữa các khung thay vì cắt cụt giờ (giờ luôn đủ HH:MM —
   * luật lưới lịch đã chốt). Ngày làm: mỗi khung một mảnh; ngày khác: một mảnh duy nhất.
   */
  parts: string[]
  /** "8 giờ"; rỗng khi không đi làm. */
  hoursText: string
  /** Nhãn phụ: "Ca xếp riêng" / tên mẫu lịch. */
  source: string
}

export function describeMyShiftDay(day: MyShiftDay): MyShiftDayView {
  const segments = day.segments.join(' · ')
  const hoursText = day.hours > 0 ? `${formatShiftHours(day.hours)} giờ` : ''
  const source = day.is_shift ? 'Ca xếp riêng' : day.schedule_name

  if (day.is_holiday) {
    const name = day.holiday_name ? `Lễ: ${day.holiday_name}` : 'Ngày lễ'
    return {
      tone: 'holiday',
      text: day.is_shift && segments ? `${name} · ${segments}` : name,
      parts: day.is_shift && segments ? [name, ...day.segments] : [name],
      hoursText: day.is_shift ? hoursText : '',
      source,
    }
  }
  if (day.is_day_off || !segments) {
    const text = day.is_shift ? 'Nghỉ (xếp ca)' : 'Nghỉ'
    return { tone: day.is_shift ? 'shift-off' : 'off', text, parts: [text], hoursText: '', source }
  }
  return { tone: day.is_shift ? 'shift' : 'work', text: segments, parts: [...day.segments], hoursText, source }
}
