import { parseLocalDate, toDateInputValue } from '@/shared/utils/format-date'

import type { ReportCompareMode } from '../types/report-analytics'

/**
 * 10 preset kỳ báo cáo — CHỈ khóa + nhãn tiếng Việt, gửi lên backend qua tham
 * số `preset`. Backend (`report_period.parse_period`) là nguồn DUY NHẤT của
 * khoảng ngày THẬT (`period.date_from/date_to` trả về sau khi gọi API) — tầng
 * này không tính lại khoảng ngày để lọc số liệu.
 */
export type ReportPresetKey =
  | 'today'
  | 'yesterday'
  | 'last_7_days'
  | 'last_30_days'
  | 'this_month'
  | 'last_month'
  | 'this_quarter'
  | 'this_year'
  | 'last_year'
  | 'custom'

export interface ReportPresetOption {
  key: ReportPresetKey
  label: string
}

/** Mặc định khi mở trang lần đầu, không có `preset` trên URL (Q0.1, 28/09/2026). */
export const DEFAULT_REPORT_PRESET: ReportPresetKey = 'this_month'

export const REPORT_PRESETS: ReportPresetOption[] = [
  { key: 'today', label: 'Hôm nay' },
  { key: 'yesterday', label: 'Hôm qua' },
  { key: 'last_7_days', label: '7 ngày qua' },
  { key: 'last_30_days', label: '30 ngày qua' },
  { key: 'this_month', label: 'Tháng này' },
  { key: 'last_month', label: 'Tháng trước' },
  { key: 'this_quarter', label: 'Quý này' },
  { key: 'this_year', label: 'Năm nay' },
  { key: 'last_year', label: 'Năm trước' },
  { key: 'custom', label: 'Tùy chọn khoảng ngày' },
]

const REPORT_PRESET_KEYS = new Set<string>(REPORT_PRESETS.map((p) => p.key))

export function isReportPresetKey(value: string | null): value is ReportPresetKey {
  return value !== null && REPORT_PRESET_KEYS.has(value)
}

function at(year: number, month: number, day: number): string {
  return toDateInputValue(new Date(year, month, day))
}

/** Cộng/trừ ngày, giữ nguyên giờ địa phương (không đụng UTC). */
function shiftDays(from: Date, days: number): Date {
  const next = new Date(from)
  next.setDate(next.getDate() + days)
  return next
}

/**
 * Khoảng ngày CỤC BỘ — chỉ dùng để MỒI ô chọn ngày lúc người dùng chuyển sang
 * "Tùy chọn khoảng ngày" (bấm chọn preset khác trước đó thì không gọi hàm này
 * — backend tính lại toàn bộ). Không dùng để lọc số liệu.
 *
 * `custom` trả về khoảng của "Tháng này" — mồi một khoảng CÓ SẴN thay vì để hai
 * ô ngày trống trơn, tránh gửi `preset=custom` không kèm ngày lên backend (dễ
 * ăn 422 theo `report_period.parse_period`, phase-01 §Requirements).
 */
export function resolveLocalPresetRange(
  preset: ReportPresetKey,
  today = new Date(),
): [string, string] {
  switch (preset) {
    case 'today':
      return [toDateInputValue(today), toDateInputValue(today)]
    case 'yesterday': {
      const y = shiftDays(today, -1)
      return [toDateInputValue(y), toDateInputValue(y)]
    }
    case 'last_7_days':
      return [toDateInputValue(shiftDays(today, -6)), toDateInputValue(today)]
    case 'last_30_days':
      return [toDateInputValue(shiftDays(today, -29)), toDateInputValue(today)]
    case 'last_month': {
      //  Tháng 0 (Giêng) lùi một tháng phải nhảy sang năm trước — `Date` tự lo
      //  việc đó nếu đưa thẳng `month - 1` vào constructor thay vì tính tay `%`.
      const firstOfLastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)
      return [
        at(firstOfLastMonth.getFullYear(), firstOfLastMonth.getMonth(), 1),
        at(firstOfLastMonth.getFullYear(), firstOfLastMonth.getMonth() + 1, 0),
      ]
    }
    case 'this_quarter': {
      const firstMonth = Math.floor(today.getMonth() / 3) * 3
      return [at(today.getFullYear(), firstMonth, 1), at(today.getFullYear(), firstMonth + 3, 0)]
    }
    case 'this_year':
      return [at(today.getFullYear(), 0, 1), at(today.getFullYear(), 11, 31)]
    case 'last_year':
      return [at(today.getFullYear() - 1, 0, 1), at(today.getFullYear() - 1, 11, 31)]
    case 'custom':
    case 'this_month':
    default:
      //  `new Date(y, m + 1, 0)` = ngày 0 của tháng sau = ngày cuối tháng này;
      //  trình duyệt tự lo tháng 28/29/30/31 ngày.
      return [
        at(today.getFullYear(), today.getMonth(), 1),
        at(today.getFullYear(), today.getMonth() + 1, 0),
      ]
  }
}

/**
 * Khoảng ngày SO SÁNH, tính CỤC BỘ — chỉ dùng để MỒI dòng "So với …" trên nút
 * mở popover kỳ TRƯỚC KHI có lượt gọi API đầu tiên (`ReportPeriodControl`); có
 * `period.compare_from/to` từ response rồi thì dùng nguyên bản đó, không dùng
 * hàm này nữa — backend là nguồn DUY NHẤT của kỳ so sánh THẬT.
 *
 * `'year'` lùi đúng một năm dương lịch (giữ tháng/ngày); `'previous'` lấy
 * khoảng LIỀN KỀ TRƯỚC, cùng số ngày.
 */
export function resolveLocalCompareRange(
  from: string,
  to: string,
  compare: ReportCompareMode,
): [string, string] | null {
  if (compare === 'none') return null
  const start = parseLocalDate(from)
  const end = parseLocalDate(to)
  if (!start || !end) return null

  if (compare === 'year') {
    const shiftYear = (d: Date) => new Date(d.getFullYear() - 1, d.getMonth(), d.getDate())
    return [toDateInputValue(shiftYear(start)), toDateInputValue(shiftYear(end))]
  }

  const lengthDays = Math.round((end.getTime() - start.getTime()) / 86_400_000) + 1
  const compareTo = shiftDays(start, -1)
  const compareFrom = shiftDays(compareTo, -(lengthDays - 1))
  return [toDateInputValue(compareFrom), toDateInputValue(compareTo)]
}
