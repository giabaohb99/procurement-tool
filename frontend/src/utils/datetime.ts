// Backend lưu thời gian theo UTC (naive, không kèm 'Z'). Khi hiển thị phải quy về giờ VN (+7),
// nếu không JS sẽ hiểu nhầm là giờ local → lệch 7 tiếng.
const VN_TZ = 'Asia/Ho_Chi_Minh'

function toDate(v: any): Date | null {
  if (!v) return null
  let s = String(v)
  // Không có thông tin timezone (Z hoặc ±HH:MM) → coi là UTC
  if (!/[zZ]$|[+-]\d{2}:?\d{2}$/.test(s)) s += 'Z'
  const d = new Date(s)
  return isNaN(d.getTime()) ? null : d
}

/** Ngày + giờ theo giờ VN, vd "09:46:41 09/07/2026". */
export function fmtDateTime(v: any): string {
  const d = toDate(v)
  return d ? d.toLocaleString('vi-VN', { timeZone: VN_TZ }) : ''
}

/** Chỉ ngày theo giờ VN. */
export function fmtDate(v: any): string {
  const d = toDate(v)
  return d ? d.toLocaleDateString('vi-VN', { timeZone: VN_TZ }) : ''
}
