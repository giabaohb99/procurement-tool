/**
 * Giờ 24h dạng "HH:MM" — KHÔNG phụ thuộc locale của trình duyệt (khác `<input type="time">`
 * hiện «08:00 AM» trên máy cài en-US). Hàm thuần, dùng cho ô nhập giờ `TimeInput24h`.
 */

/** Che lúc gõ: chỉ giữ chữ số, tối đa 4, tự chèn «:» sau hai số đầu. «830» -> «08:30» làm ở `parseTime24h`. */
export function maskTime24h(raw: string): string {
  //  «8:» = người gõ ngắt giờ một chữ số bằng dấu «:» -> hiểu là «08», nếu không «8:30» ra «83:0».
  const lead = /^(\d):/.exec(raw)
  const digits = (lead ? `0${raw}` : raw).replace(/\D/g, '').slice(0, 4)
  return digits.length > 2 ? `${digits.slice(0, 2)}:${digits.slice(2)}` : digits
}

/**
 * Đọc chữ người gõ thành "HH:MM" hợp lệ, không đọc được (hoặc giờ > 23, phút > 59) thì `null`.
 * Chấp nhận «8», «830», «8:30», «0830», «08:30». Một hoặc hai chữ số = số giờ tròn («8» -> 08:00).
 */
export function parseTime24h(text: string): string | null {
  const trimmed = text.trim()
  const colon = /^(\d{1,2}):(\d{1,2})$/.exec(trimmed)
  let hour: number
  let minute: number
  if (colon) {
    hour = Number(colon[1])
    minute = Number(colon[2].padEnd(2, '0'))
  } else if (/^\d{1,2}$/.test(trimmed)) {
    hour = Number(trimmed)
    minute = 0
  } else if (/^\d{3,4}$/.test(trimmed)) {
    const padded = trimmed.padStart(4, '0')
    hour = Number(padded.slice(0, 2))
    minute = Number(padded.slice(2))
  } else {
    return null
  }
  if (hour > 23 || minute > 59) return null
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
}

/** Cộng/trừ phút vào "HH:MM", kẹp trong 00:00–23:59 (không quay vòng qua nửa đêm). Giờ hỏng -> 00:00 + delta. */
export function shiftTime24h(value: string | null, deltaMinutes: number): string {
  const parsed = value ? parseTime24h(value) : null
  const base = parsed ? Number(parsed.slice(0, 2)) * 60 + Number(parsed.slice(3)) : 0
  const next = Math.min(23 * 60 + 59, Math.max(0, base + deltaMinutes))
  return `${String(Math.floor(next / 60)).padStart(2, '0')}:${String(next % 60).padStart(2, '0')}`
}
