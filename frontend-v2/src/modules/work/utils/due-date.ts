/**
 * Hạn chót trên thẻ việc: hiện gì và tô màu gì.
 *
 * Hạn lưu dạng chuỗi `"YYYY-MM-DD"` (quyết định §0.2 của `02-bang-du-lieu.md`)
 * nên **so sánh bằng chuỗi**, không dựng `Date` rồi so mốc thời gian: dựng
 * `new Date("2026-08-28")` là mốc UTC, ở múi giờ +07 lùi về hôm trước và hạn
 * hôm nay bỗng thành quá hạn.
 */

/** Hôm nay dạng `"YYYY-MM-DD"` theo giờ MÁY NGƯỜI DÙNG, không phải UTC. */
export function today(): string {
  const d = new Date()
  const thang = `${d.getMonth() + 1}`.padStart(2, '0')
  const ngay = `${d.getDate()}`.padStart(2, '0')
  return `${d.getFullYear()}-${thang}-${ngay}`
}

export type DueTone = 'overdue' | 'today' | 'soon' | 'normal' | 'none'

/** Sắc thái của hạn so với hôm nay — quyết định màu chữ trên thẻ (§4). */
export function dueTone(due: string, doneAlready = false): DueTone {
  if (!due) return 'none'
  if (doneAlready) return 'normal'
  const hom_nay = today()
  if (due < hom_nay) return 'overdue'
  if (due === hom_nay) return 'today'
  return 'normal'
}

export function dueToneClass(tone: DueTone): string {
  if (tone === 'overdue') return 'text-red-600 dark:text-red-400'
  if (tone === 'today') return 'text-orange-600 dark:text-orange-400'
  return 'text-muted-foreground'
}

/** `"2026-08-28"` → `"28/08"`, khác năm hiện tại thì kèm năm. */
export function formatDueLabel(due: string): string {
  if (!due || due.length !== 10) return ''
  const [nam, thang, ngay] = due.split('-')
  const namNay = today().slice(0, 4)
  return nam === namNay ? `${ngay}/${thang}` : `${ngay}/${thang}/${nam}`
}

/** Cộng thêm `n` ngày vào hôm nay, trả về chuỗi `"YYYY-MM-DD"` (nút Hôm nay / Ngày mai). */
export function addDays(n: number): string {
  const d = new Date()
  d.setDate(d.getDate() + n)
  const thang = `${d.getMonth() + 1}`.padStart(2, '0')
  const ngay = `${d.getDate()}`.padStart(2, '0')
  return `${d.getFullYear()}-${thang}-${ngay}`
}
