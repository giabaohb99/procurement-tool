import { formatDate } from '@/shared/utils/format-date'

/**
 * METADATA CỦA GIẤY NGHỈ PHÉP (GNP) ngoài mười ô của form (duoc-CR-683).
 *
 * Giấy GNP do hệ tự sinh khi đơn nghỉ được duyệt (`leave/approval_bridge.py`) mang thêm vài khóa
 * form văn bản không có ô nhập: `leave_periods` (đơn nhiều khoảng ngày), `leave_lines` (đơn
 * nhiều loại nghỉ). Backend GHI ĐÈ cả `metadata` mỗi lần lưu văn bản, nên form phải giữ nguyên
 * các khóa đó rồi gửi lại — không thì sửa một chữ ở lý do là giấy mất luôn bản kê khoảng ngày.
 */

/** Mười khóa form văn bản có ô nhập — khớp khối `leave` ở `document-record-schema.ts`. */
const LEAVE_FORM_KEYS = new Set([
  'employee_id',
  'leave_type',
  'from_date',
  'from_session',
  'to_date',
  'to_session',
  'total_days',
  'reason',
  'handover_employee_id',
  'contact_phone',
])

/** Các khóa metadata NGOÀI mười ô của form — giữ nguyên để lưu lại không làm rơi. */
export function leaveExtraOf(metadata: Record<string, unknown> | null | undefined) {
  return Object.fromEntries(
    Object.entries(metadata ?? {}).filter(([key]) => !LEAVE_FORM_KEYS.has(key)),
  )
}

/** Một khoảng ngày trên giấy GNP — buổi là MÃ CHUỖI (`full` · `morning` · `afternoon`). */
export interface GnpLeavePeriod {
  from_date: string
  from_session: string
  to_date: string
  to_session: string
  days: number
}

/**
 * Bản kê khoảng ngày của giấy, chỉ khi có TỪ HAI khoảng (đơn một khoảng thì hai ô Từ/Đến ngày
 * đã đủ). Phần tử hỏng bị bỏ qua: đây là bản chép để đọc, không phải chỗ kiểm dữ liệu.
 */
export function gnpLeavePeriodsOf(extra: Record<string, unknown> | undefined): GnpLeavePeriod[] {
  const raw = extra?.leave_periods
  if (!Array.isArray(raw)) return []
  const periods = raw.flatMap((item): GnpLeavePeriod[] => {
    if (!item || typeof item !== 'object') return []
    const p = item as Record<string, unknown>
    if (typeof p.from_date !== 'string' || typeof p.to_date !== 'string') return []
    return [
      {
        from_date: p.from_date,
        from_session: String(p.from_session ?? 'full'),
        to_date: p.to_date,
        to_session: String(p.to_session ?? 'full'),
        days: Number(p.days) || 0,
      },
    ]
  })
  return periods.length > 1 ? periods : []
}

const SESSION_TEXT: Record<string, string> = {
  full: 'cả ngày',
  morning: 'sáng',
  afternoon: 'chiều',
}

function sessionText(code: string): string {
  return SESSION_TEXT[code] ?? SESSION_TEXT.full
}

/**
 * Một dòng chữ cho một khoảng: "27/10/2026 (cả ngày) · 1 ngày",
 * "03/11/2026 (chiều) → 07/11/2026 (cả ngày) · 4.5 ngày".
 */
export function formatGnpLeavePeriod(p: GnpLeavePeriod): string {
  const days = `${p.days} ngày`
  if (p.from_date === p.to_date) {
    const session =
      p.from_session === p.to_session
        ? sessionText(p.from_session)
        : `${sessionText(p.from_session)} → ${sessionText(p.to_session)}`
    return `${formatDate(p.from_date)} (${session}) · ${days}`
  }
  return (
    `${formatDate(p.from_date)} (${sessionText(p.from_session)}) → ` +
    `${formatDate(p.to_date)} (${sessionText(p.to_session)}) · ${days}`
  )
}
