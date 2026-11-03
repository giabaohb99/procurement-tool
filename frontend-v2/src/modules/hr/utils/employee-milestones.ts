import { parseLocalDate } from '@/shared/utils/format-date'

/**
 * Mốc của một nhân sự hiện ở thanh bên màn chi tiết (duoc-CR-708, học theo
 * ERPNext `employee.js` → `add_anniversary_indicator`).
 *
 * - `isBirthday`: hôm nay trùng ngày-tháng sinh.
 * - `anniversaryYears`: hôm nay trùng ngày-tháng vào làm VÀ đã tròn ít nhất 1 năm;
 *   `0` = không phải ngày kỷ niệm (ngày vào làm đầu tiên không tính là kỷ niệm).
 * - `tenure`: thâm niên tính tới hôm nay; `null` khi chưa khai ngày vào làm hoặc
 *   ngày vào làm nằm ở tương lai.
 */
export interface EmployeeMilestones {
  isBirthday: boolean
  anniversaryYears: number
  tenure: { years: number; months: number } | null
}

/**
 * Ngày 29/02 ở năm KHÔNG nhuận thì coi 28/02 là ngày kỷ niệm — ERPNext so thẳng
 * ngày-tháng nên người sinh 29/02 chỉ có sinh nhật bốn năm một lần.
 */
function isSameDayOfYear(origin: Date, today: Date): boolean {
  if (origin.getMonth() !== today.getMonth()) return false
  if (origin.getDate() === today.getDate()) return true
  const isLeapDay = origin.getMonth() === 1 && origin.getDate() === 29
  const februaryEnd = new Date(today.getFullYear(), 2, 0).getDate()
  return isLeapDay && februaryEnd === 28 && today.getDate() === 28
}

/**
 * Số tháng TRÒN từ `from` tới `to` (chưa tới ngày trong tháng thì chưa tính tháng đó).
 *
 * Ngày vào làm lớn hơn số ngày của tháng đích (31/01 → tháng 4, 29/02 → năm thường)
 * thì coi NGÀY CUỐI tháng là đã tròn — cùng luật với `isSameDayOfYear`, nếu không thì
 * 28/02/2025 vừa hiện "Tròn 1 năm làm việc" vừa hiện thâm niên "11 tháng".
 */
function countFullMonths(from: Date, to: Date): number {
  const months = (to.getFullYear() - from.getFullYear()) * 12 + (to.getMonth() - from.getMonth())
  const monthEnd = new Date(to.getFullYear(), to.getMonth() + 1, 0).getDate()
  return to.getDate() < Math.min(from.getDate(), monthEnd) ? months - 1 : months
}

/**
 * Tính các mốc từ ngày sinh và ngày vào làm (`YYYY-MM-DD`).
 *
 * ⚠️ `dateOfBirth` là trường NHẠY CẢM: người không có `employee_sensitive.read`
 * nhận chuỗi rỗng / `null` từ backend, nên ở đó không bao giờ hiện "Sinh nhật"
 * — đúng ý, đừng tìm cách suy ngày sinh từ chỗ khác.
 */
export function computeEmployeeMilestones(
  dateOfBirth: string | null | undefined,
  hireDate: string | null | undefined,
  today: Date,
): EmployeeMilestones {
  //  "Hôm nay" theo giờ TRÌNH DUYỆT — người dùng ở Việt Nam nên trùng `vn_today()` của
  //  backend; máy đặt múi giờ khác thì mốc có thể lệch một ngày (chỉ là dòng hiển thị).
  const birth = parseLocalDate(dateOfBirth)
  const hire = parseLocalDate(hireDate)
  const day = new Date(today.getFullYear(), today.getMonth(), today.getDate())

  const isBirthday = !!birth && birth <= day && isSameDayOfYear(birth, day)

  let anniversaryYears = 0
  let tenure: EmployeeMilestones['tenure'] = null
  if (hire && hire <= day) {
    const months = countFullMonths(hire, day)
    tenure = { years: Math.floor(months / 12), months: months % 12 }
    const years = day.getFullYear() - hire.getFullYear()
    if (years > 0 && isSameDayOfYear(hire, day)) anniversaryYears = years
  }

  return { isBirthday, anniversaryYears, tenure }
}

/** "3 năm 2 tháng" · "5 tháng" · "Dưới 1 tháng". */
export function formatTenure(tenure: { years: number; months: number }): string {
  const parts: string[] = []
  if (tenure.years > 0) parts.push(`${tenure.years} năm`)
  if (tenure.months > 0) parts.push(`${tenure.months} tháng`)
  return parts.length > 0 ? parts.join(' ') : 'Dưới 1 tháng'
}
