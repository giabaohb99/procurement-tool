/**
 * Phép tính thuần của khung demo theo chương (ai-CR-214, K8 doc/erp/21 §6.4).
 *
 * Mọi chuyển động của một chương suy ra từ MỘT con số `progress` (0 → 1): con trỏ
 * giả đang ở đâu, đã gõ tới chữ nào, hộp thoại đã nổi lên chưa. Nhờ vậy tạm dừng,
 * nhảy chương hay chế độ giảm chuyển động (`progress = 1`, ảnh tĩnh) đều chỉ là đặt
 * lại con số đó — không có hẹn giờ nào chạy riêng trong từng cảnh.
 */

/** Một mốc của con trỏ giả: `at` là tiến độ chương (0 → 1), `x` / `y` là % khung. */
export interface CursorPoint {
  at: number
  x: number
  y: number
  click?: boolean
}

export interface CursorState {
  x: number
  y: number
  clicking: boolean
}

/** Khoảng tiến độ quanh một mốc `click` mà con trỏ hiện vòng bấm. */
export const CLICK_WINDOW = 0.04

export function clampProgress(value: number): number {
  if (!Number.isFinite(value)) return 0
  return Math.min(1, Math.max(0, value))
}

/** Vị trí con trỏ tại `progress`: nội suy thẳng giữa hai mốc kề nhau; trước mốc đầu / sau mốc cuối thì đứng yên. */
export function cursorAt(path: readonly CursorPoint[], progress: number): CursorState | null {
  if (path.length === 0) return null
  const p = clampProgress(progress)
  const points = [...path].sort((a, b) => a.at - b.at)
  const clicking = points.some((pt) => pt.click && p >= pt.at && p < pt.at + CLICK_WINDOW)
  const first = points[0]
  const last = points[points.length - 1]
  if (p <= first.at) return { x: first.x, y: first.y, clicking }
  if (p >= last.at) return { x: last.x, y: last.y, clicking }
  for (let i = 1; i < points.length; i += 1) {
    const a = points[i - 1]
    const b = points[i]
    if (p <= b.at) {
      const span = b.at - a.at
      const t = span <= 0 ? 1 : (p - a.at) / span
      return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, clicking }
    }
  }
  return { x: last.x, y: last.y, clicking }
}

/** Phần chữ đã "gõ" tới `progress`, gõ đều từ `from` tới `to` (tiến độ chương). */
export function typedText(full: string, progress: number, from = 0, to = 1): string {
  const p = clampProgress(progress)
  if (to <= from) return p >= from ? full : ''
  if (p <= from) return ''
  if (p >= to) return full
  const chars = Array.from(full)
  return chars.slice(0, Math.round(((p - from) / (to - from)) * chars.length)).join('')
}

/** Đã qua mốc `at` chưa (hộp thoại mở, bước đã xong…). */
export function reached(progress: number, at: number): boolean {
  return clampProgress(progress) >= at
}

/** Số chương hiển thị hai chữ số: 0 → "01". */
export function chapterNumber(index: number): string {
  return String(Math.max(0, Math.trunc(index)) + 1).padStart(2, '0')
}
