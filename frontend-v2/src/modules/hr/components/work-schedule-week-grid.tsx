import type { WorkScheduleDay } from '../types/work-schedule'
import { WEEKDAY_LABELS, fillWeek, presentWeekdays } from '../utils/work-schedule-week'
import { describeDay, describeLunch } from '../utils/work-schedule-week-summary'

/** Thứ nào backend không trả thì không có trong Map -> ô hiện "—", không bịa thành "Nghỉ". */
function indexByWeekday(days: unknown): Map<number, WorkScheduleDay> {
  const present = presentWeekdays(days)
  return new Map(fillWeek(days).filter((d) => present.has(d.weekday)).map((d) => [d.weekday, d]))
}

interface WorkScheduleWeekGridProps {
  /** Bảy ngày của mẫu lịch như backend trả; thiếu / hỏng ngày nào thì ô đó hiện "—". */
  days: unknown
}

/**
 * Lưới CHỈ XEM bảy ngày (T2 → CN) của một mẫu lịch: giờ làm + giờ nghỉ trưa từng ngày.
 * Dùng chung cho thẻ Lịch làm việc ở hồ sơ nhân sự và tab Lịch làm việc của phòng ban.
 * Khổ hẹp xếp 4 cột, từ `sm` đủ 7 cột một hàng.
 */
export function WorkScheduleWeekGrid({ days }: WorkScheduleWeekGridProps) {
  const byWeekday = indexByWeekday(days)
  return (
    <ul className="grid grid-cols-4 gap-2 text-center text-sm sm:grid-cols-7">
      {WEEKDAY_LABELS.map((label, weekday) => {
        const day = byWeekday.get(weekday)
        const lunch = day ? describeLunch(day) : ''
        return (
          <li key={label} className="rounded-md border px-1 py-2">
            <div className="text-xs font-semibold text-muted-foreground">{label}</div>
            <div className="font-medium">{day ? describeDay(day) : '—'}</div>
            {lunch && <div className="text-xs text-muted-foreground">{lunch}</div>}
          </li>
        )
      })}
    </ul>
  )
}
