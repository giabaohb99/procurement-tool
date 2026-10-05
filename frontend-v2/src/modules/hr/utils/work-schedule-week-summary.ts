import { WORK_DAY_KIND_CODE, type WorkScheduleDay } from '../types/work-schedule'
import { STANDARD_LUNCH, WEEKDAY_LABELS, fillWeek, presentWeekdays } from './work-schedule-week'

function hours(day: WorkScheduleDay): string {
  return day.start_time && day.end_time ? `${day.start_time}–${day.end_time}` : ''
}

/** «nghỉ trưa 12:00–13:00» của ngày Cả ngày có khai giờ trưa; ngày khác -> chuỗi rỗng. */
export function describeLunch(day: WorkScheduleDay): string {
  if (day.day_kind !== WORK_DAY_KIND_CODE.FULL) return ''
  return day.lunch_start && day.lunch_end ? `nghỉ trưa ${day.lunch_start}–${day.lunch_end}` : ''
}

/**
 * Nhãn ngắn của MỘT ngày, luôn kèm giờ khi có: «08:00–17:00», «Sáng 08:00–12:00»,
 * «Chiều 13:00–17:00», «Nghỉ». Giờ nghỉ trưa ở `describeLunch` (thẻ hẹp bày riêng).
 */
export function describeDay(day: WorkScheduleDay): string {
  const range = hours(day)
  if (day.day_kind === WORK_DAY_KIND_CODE.FULL) return range || 'Cả ngày'
  if (day.day_kind === WORK_DAY_KIND_CODE.MORNING) return range ? `Sáng ${range}` : 'Sáng'
  if (day.day_kind === WORK_DAY_KIND_CODE.AFTERNOON) return range ? `Chiều ${range}` : 'Chiều'
  return 'Nghỉ'
}

/** Nhãn đầy đủ cho ô chỉ xem: «08:00–17:00 (nghỉ trưa 12:00–13:00)». */
export function describeDayFull(day: WorkScheduleDay): string {
  const lunch = describeLunch(day)
  return lunch ? `${describeDay(day)} (${lunch})` : describeDay(day)
}

/**
 * Nhãn trong bản tóm tắt tuần. Giờ trưa chuẩn 12:00–13:00 thì lược đi cho gọn;
 * khác chuẩn hoặc không nghỉ trưa thì NÓI RA — nếu không, hai nhóm cùng «08:00–17:00»
 * liền nhau sẽ trông như bị lặp mà không ai hiểu vì sao tách.
 */
function describeForSummary(day: WorkScheduleDay): string {
  const base = describeDay(day).toLocaleLowerCase('vi-VN')
  if (day.day_kind !== WORK_DAY_KIND_CODE.FULL || !hours(day)) return base
  if (!day.lunch_start || !day.lunch_end) return `${base} (không nghỉ trưa)`
  const standard = day.lunch_start === STANDARD_LUNCH.start && day.lunch_end === STANDARD_LUNCH.end
  return standard ? base : `${base} (${describeLunch(day)})`
}

/**
 * Tóm tắt tuần: «T2–T6 08:00–17:00 · T7 sáng 08:00–12:00 · CN nghỉ».
 * Chỉ gom các thứ LIỀN NHAU có cùng loại, cùng giờ làm và cùng giờ trưa (T2,T4 cách
 * quãng thì không gom). Toàn Nghỉ -> «Nghỉ cả tuần»; không có ngày nào -> «Chưa khai lịch».
 */
export function summarizeWeek(days: unknown): string {
  if (!Array.isArray(days) || days.length === 0) return 'Chưa khai lịch'
  const week = fillWeek(days)
  const present = presentWeekdays(days)
  if (present.size === 0) return 'Chưa khai lịch'
  if (present.size === 7 && week.every((day) => day.day_kind === WORK_DAY_KIND_CODE.OFF)) {
    return 'Nghỉ cả tuần'
  }

  const parts: string[] = []
  let index = 0
  while (index < week.length) {
    // Thứ chưa khai thì bỏ qua, không tự bịa là «nghỉ».
    if (!present.has(index)) {
      index += 1
      continue
    }
    const label = describeForSummary(week[index])
    let end = index
    while (
      end + 1 < week.length &&
      present.has(end + 1) &&
      week[end + 1].day_kind === week[index].day_kind &&
      describeForSummary(week[end + 1]) === label
    ) {
      end += 1
    }
    const range =
      end === index ? WEEKDAY_LABELS[index] : `${WEEKDAY_LABELS[index]}–${WEEKDAY_LABELS[end]}`
    parts.push(`${range} ${label}`)
    index = end + 1
  }
  return parts.join(' · ')
}
