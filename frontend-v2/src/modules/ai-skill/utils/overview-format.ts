/** Định dạng số liệu màn Tổng quan Kho skill AI (G1). */

/** Câu so sánh 7 ngày — `null` (7 ngày trước bằng 0) thì không nói phần trăm, khỏi in "+Infinity%". */
export function describeChange(pct: number | null, previous: number): string {
  if (pct === null) return previous === 0 ? '7 ngày trước chưa có lượt nào' : ''
  if (!Number.isFinite(pct)) return ''
  if (pct === 0) return 'bằng 7 ngày trước'
  return `${pct > 0 ? '+' : ''}${pct.toLocaleString('vi-VN', { maximumFractionDigits: 1 })}% so với 7 ngày trước`
}

/** % đổi so với kỳ trước, làm tròn 1 chữ số; kỳ trước bằng 0 (hoặc số hỏng) → `null`, để `describeChange` nói bằng lời. */
export function computeChangePct(current: number, previous: number): number | null {
  if (!Number.isFinite(current) || !Number.isFinite(previous) || previous <= 0) return null
  return Math.round(((current - previous) / previous) * 1000) / 10
}

/** Nhãn trục ngày: `2026-10-17` → `17/10` (cắt chuỗi, không qua `Date` để khỏi lệch múi giờ). */
export function shortDay(day: string): string {
  const [, month, date] = day.split('-')
  return month && date ? `${date}/${month}` : day
}
