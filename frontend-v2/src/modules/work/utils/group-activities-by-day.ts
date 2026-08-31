import type { WorkActivity } from '../types/activity'

/**
 * Một mốc ngày trên dòng hoạt động — cột ngày bên trái + các dòng của ngày đó.
 *
 * Cột ngày vẽ hai tầng theo khuôn Lark: chữ nhỏ ở trên (`Hôm nay`, `Th 8`) và
 * SỐ NGÀY to bên dưới, nên hai phần tách riêng chứ không ghép sẵn một chuỗi.
 */
export interface ActivityDay {
  /** Khóa `YYYY-MM-DD` theo giờ ĐỊA PHƯƠNG — dùng làm React `key`. */
  key: string
  /** Chữ nhỏ: `Hôm nay` · `Hôm qua` · `Th 8` · `Th 8, 2025`. */
  label: string
  /** Số ngày trong tháng, `01`…`31`. Rỗng khi mốc thời gian hỏng. */
  dayNumber: string
  items: WorkActivity[]
}

/**
 * Gom dòng hoạt động theo NGÀY, giữ nguyên thứ tự backend trả (mới nhất trước).
 *
 * Vì sao gom ở đây chứ không để backend gom: các trang được lấy dần khi cuộn,
 * mà một ngày rất dễ vắt qua hai trang — backend gom thì cuộn xuống sẽ thấy hai
 * mốc "Hôm nay" nằm liền nhau.
 *
 * `now` truyền được từ ngoài để test khỏi phụ thuộc "hôm nay" thật.
 */
export function groupActivitiesByDay(
  items: WorkActivity[],
  now: Date = new Date(),
): ActivityDay[] {
  const days: ActivityDay[] = []
  for (const item of items) {
    const date = parseMoment(item.at)
    //  Mốc hỏng (chuỗi rỗng / sai dạng) vẫn phải hiện: gom vào một mốc riêng
    //  chứ đừng lặng lẽ nuốt dòng — mất một dòng nhật ký là mất dấu vết.
    const key = date ? dayKey(date) : ''
    const last = days[days.length - 1]
    if (last && last.key === key) {
      last.items.push(item)
      continue
    }
    days.push({
      key,
      label: date ? dayLabel(date, now) : 'Không rõ thời điểm',
      dayNumber: date ? String(date.getDate()).padStart(2, '0') : '',
      items: [item],
    })
  }
  return days
}

/**
 * Chữ nhỏ trên số ngày: `Hôm nay` / `Hôm qua` cho hai ngày gần nhất, còn lại là
 * tháng — kèm NĂM khi khác năm hiện tại, không thì tháng 8 năm ngoái và tháng 8
 * năm nay trông y hệt nhau.
 */
function dayLabel(date: Date, now: Date): string {
  const diff = daysBetween(dayKey(date), dayKey(now))
  if (diff === 0) return 'Hôm nay'
  if (diff === 1) return 'Hôm qua'
  const thang = `Th ${date.getMonth() + 1}`
  return date.getFullYear() === now.getFullYear() ? thang : `${thang}, ${date.getFullYear()}`
}

function dayKey(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

/**
 * Số ngày LỊCH giữa hai khóa `YYYY-MM-DD`.
 *
 * Trừ hai mốc `Date` rồi chia 86400000 là sai vào ngày đổi giờ mùa hè và sai
 * mỗi khi hai mốc lệch nhau vài giờ trong cùng một ngày.
 */
function daysBetween(from: string, to: string): number {
  const a = Date.UTC(+from.slice(0, 4), +from.slice(5, 7) - 1, +from.slice(8, 10))
  const b = Date.UTC(+to.slice(0, 4), +to.slice(5, 7) - 1, +to.slice(8, 10))
  return Math.round((b - a) / 86_400_000)
}

/**
 * Mốc thời gian của một dòng nhật ký → `Date` giờ máy.
 *
 * Backend trả chuỗi ISO KHÔNG hậu tố múi giờ nhưng lưu theo UTC; không gắn `Z`
 * là mọi mốc lệch đúng 7 tiếng, đủ để một dòng lúc 1h sáng rơi về "Hôm qua".
 * Cùng luật với `toDate` của `@/shared/utils/format-date`.
 */
function parseMoment(value: string | null | undefined): Date | null {
  if (!value) return null
  const hasTime = /\d{2}:\d{2}/.test(value)
  const hasZone = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(value)
  const date = new Date(hasTime && !hasZone ? `${value}Z` : value)
  return Number.isNaN(date.getTime()) ? null : date
}
