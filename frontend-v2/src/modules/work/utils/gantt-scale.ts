import type { WorkTask } from '../types/work'
import { today } from './due-date'

/**
 * Thang thời gian của khung nhìn Gantt (D-05).
 *
 * Toàn hàm THUẦN, làm việc trên chuỗi `"YYYY-MM-DD"` — cùng dạng dữ liệu backend
 * lưu (`02-bang-du-lieu.md` §0.2). Cố ý KHÔNG đổi qua `Date` để so sánh: dựng
 * `new Date("2026-08-28")` ra mốc UTC, ở múi giờ +07 nó lùi về hôm trước và cả
 * dải thanh Gantt lệch đúng một ngày. `Date` chỉ dùng ở chỗ CỘNG NGÀY, nơi phải
 * biết tháng nào 30 hay 31 ngày.
 */

export type GanttZoom = 'day' | 'week' | 'month'

/** Bề rộng MỘT ngày (px) theo mức phóng. Cả lưới nền lẫn thanh đều theo số này. */
export const DAY_WIDTH: Record<GanttZoom, number> = { day: 40, week: 14, month: 5 }

export const ZOOM_LABELS: Record<GanttZoom, string> = {
  day: 'Ngày',
  week: 'Tuần',
  month: 'Tháng',
}

const THU = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']

/** `"2026-08-28"` + n ngày → `"YYYY-MM-DD"`. Dùng `Date` local, không UTC. */
export function shiftDate(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number)
  const date = new Date(y, m - 1, d + days)
  return toIso(date)
}

function toIso(date: Date): string {
  const thang = `${date.getMonth() + 1}`.padStart(2, '0')
  const ngay = `${date.getDate()}`.padStart(2, '0')
  return `${date.getFullYear()}-${thang}-${ngay}`
}

/** Số ngày từ `a` tới `b` (b sau a thì dương). Bỏ qua giờ nên không lệch do DST. */
export function daysBetween(a: string, b: string): number {
  const [ya, ma, da] = a.split('-').map(Number)
  const [yb, mb, db] = b.split('-').map(Number)
  const msMotNgay = 86_400_000
  return Math.round((Date.UTC(yb, mb - 1, db) - Date.UTC(ya, ma - 1, da)) / msMotNgay)
}

export interface GanttTimeline {
  /** Ngày đầu và ngày cuối của dải (đã đệm hai bên). */
  start: string
  end: string
  /** Mỗi phần tử là MỘT ngày trong dải, theo thứ tự. */
  days: string[]
  dayWidth: number
  totalWidth: number
}

/** Số ngày tối thiểu của dải — dải quá ngắn thì thanh nào cũng chiếm cả màn hình. */
const MIN_DAYS = 21
/** Đệm hai bên cho thanh không dính mép. */
const PAD_DAYS = 3

/**
 * Dải thời gian đủ chứa mọi việc CÓ NGÀY, luôn bao gồm hôm nay.
 *
 * Luôn kéo dải qua hôm nay kể cả khi mọi việc đều ở quá khứ: vạch "hôm nay" là
 * thứ người dùng lấy làm mốc đọc, thiếu nó thì biểu đồ trôi lơ lửng.
 */
export function buildTimeline(
  tasks: WorkTask[],
  zoom: GanttZoom,
  homNay: string = today(),
): GanttTimeline {
  const moc: string[] = [homNay]
  for (const t of tasks) {
    if (t.start_date) moc.push(t.start_date)
    if (t.due_date) moc.push(t.due_date)
  }
  moc.sort()

  const start = shiftDate(moc[0], -PAD_DAYS)
  let end = shiftDate(moc[moc.length - 1], PAD_DAYS)
  const thieu = MIN_DAYS - (daysBetween(start, end) + 1)
  if (thieu > 0) end = shiftDate(end, thieu)

  const days: string[] = []
  for (let i = 0; i <= daysBetween(start, end); i += 1) days.push(shiftDate(start, i))

  const dayWidth = DAY_WIDTH[zoom]
  return { start, end, days, dayWidth, totalWidth: days.length * dayWidth }
}

export interface GanttBar {
  left: number
  width: number
}

/**
 * Vị trí và bề rộng thanh của một việc. `null` = việc chưa có ngày nào, không vẽ.
 *
 * Chỉ có hạn mà không có ngày bắt đầu (phần lớn dữ liệu thật) thì vẽ thanh MỘT
 * NGÀY tại đúng hạn — coi như mốc, không tự bịa ra độ dài.
 */
export function barGeometry(task: WorkTask, timeline: GanttTimeline): GanttBar | null {
  const dau = task.start_date || task.due_date
  const cuoi = task.due_date || task.start_date
  if (!dau || !cuoi) return null

  //  Ngày bắt đầu sau hạn (dữ liệu nhập ngược) thì đảo lại cho thanh vẫn vẽ được
  //  thay vì ra bề rộng âm và biến mất.
  const tu = dau <= cuoi ? dau : cuoi
  const den = dau <= cuoi ? cuoi : dau

  const left = daysBetween(timeline.start, tu) * timeline.dayWidth
  const width = (daysBetween(tu, den) + 1) * timeline.dayWidth
  return { left, width }
}

export interface GanttHeaderCell {
  key: string
  label: string
  /** Bề rộng (px) — cột đầu/cuối có thể ngắn hơn vì dải cắt giữa tháng/tuần. */
  width: number
}

/**
 * Hàng tiêu đề TRÊN: gom ngày thành tháng (mức Ngày/Tuần) hoặc năm (mức Tháng).
 * Hàng DƯỚI (`dayCells`) chỉ có ở mức Ngày — mức xa hơn thì ô một ngày quá hẹp
 * để in chữ.
 */
export function groupHeader(timeline: GanttTimeline, zoom: GanttZoom): GanttHeaderCell[] {
  const nhom = new Map<string, number>()
  for (const ngay of timeline.days) {
    const key = zoom === 'month' ? ngay.slice(0, 4) : ngay.slice(0, 7)
    nhom.set(key, (nhom.get(key) ?? 0) + 1)
  }
  return [...nhom.entries()].map(([key, soNgay]) => ({
    key,
    label: zoom === 'month' ? `Năm ${key}` : `Tháng ${Number(key.slice(5))}/${key.slice(0, 4)}`,
    width: soNgay * timeline.dayWidth,
  }))
}

/** Nhãn ô ngày ở hàng dưới: `"28 T6"` — số ngày + thứ. Chỉ dùng ở mức Ngày. */
export function dayLabel(iso: string): { so: string; thu: string } {
  const [y, m, d] = iso.split('-').map(Number)
  return { so: `${d}`, thu: THU[new Date(y, m - 1, d).getDay()] }
}

/** Cuối tuần tô nhạt cho dễ đọc dải ngày. */
export function isWeekend(iso: string): boolean {
  const [y, m, d] = iso.split('-').map(Number)
  const thu = new Date(y, m - 1, d).getDay()
  return thu === 0 || thu === 6
}
