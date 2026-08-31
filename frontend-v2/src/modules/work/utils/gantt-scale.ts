import type { WorkTask } from '../types/work'
import { WORK_TASK_KIND } from '../types/work'
import { today } from './due-date'

/**
 * Thang thời gian của khung nhìn Gantt (D-05).
 *
 * Toàn hàm THUẦN, làm việc trên chuỗi `"YYYY-MM-DD"` — cùng dạng dữ liệu backend
 * lưu (`02-bang-du-lieu.md` §0.2). Cố ý KHÔNG đổi qua `Date` để so sánh: dựng
 * `new Date("2026-08-28")` ra mốc UTC, ở múi giờ +07 nó lùi về hôm trước và cả
 * dải thanh Gantt lệch đúng một ngày. `Date` chỉ dùng ở chỗ CỘNG NGÀY và hỏi
 * THỨ, nơi phải biết tháng nào 30 hay 31 ngày.
 */

export type GanttZoom = 'day' | 'week' | 'month'

/**
 * Bề rộng MỘT ngày (px) theo mức phóng. Cả lưới nền lẫn thanh đều theo số này.
 *
 * Chọn theo bề rộng của một Ô ĐỌC ĐƯỢC ở mỗi mức, không phải theo cảm giác:
 * mức Tuần cần ~91px cho một cột tuần (đủ chỗ cho "T.37"), mức Tháng cần ~120px
 * cho một cột tháng. Số lẻ thì mép ô lệch dần và cuối biểu đồ trượt khỏi lưới.
 */
/**
 * Bề rộng MỘT NGÀY theo từng mức phóng, tính bằng px.
 *
 * Mức Ngày nới 38 → 44 → 56 → **64** (khách 31/08/2026, ba lượt): 38px hẹp hơn
 * cả chiều cao hàng nên lưới nhìn dẹt và bị nén; 44 mới vừa vuông; 56 vẫn chưa
 * đủ chỗ cho hai dòng «21 / T3» thở.
 *
 * ⚠️ Con số này nhân thẳng với 730 ngày của khung hai năm (`khungToiThieu`):
 * 64 × 730 ≈ **46.700px** bề rộng nội dung. Vẫn chịu được vì lưới nền vẽ theo Ô
 * của hàng tiêu đề chứ không theo từng ngày (một ô = một tháng ở hàng trên, một
 * ngày ở hàng dưới), nhưng số ô của hàng dưới thì đúng bằng số ngày — nới thêm
 * nữa là phải đo lại thời gian vẽ, đừng nâng mù.
 */
export const DAY_WIDTH: Record<GanttZoom, number> = { day: 64, week: 13, month: 4 }

export const ZOOM_LABELS: Record<GanttZoom, string> = {
  day: 'Ngày',
  week: 'Tuần',
  month: 'Tháng',
}

const THU = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']

/** `"2026-08-28"` + n ngày → `"YYYY-MM-DD"`. Dùng `Date` local, không UTC. */
export function shiftDate(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number)
  return toIso(new Date(y, m - 1, d + days))
}

function toIso(date: Date): string {
  const thang = `${date.getMonth() + 1}`.padStart(2, '0')
  const ngay = `${date.getDate()}`.padStart(2, '0')
  return `${date.getFullYear()}-${thang}-${ngay}`
}

/** Thứ trong tuần theo chuẩn JS: 0 = Chủ nhật … 6 = thứ Bảy. */
function weekday(iso: string): number {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).getDay()
}

/** Số ngày từ `a` tới `b` (b sau a thì dương). Bỏ qua giờ nên không lệch do DST. */
export function daysBetween(a: string, b: string): number {
  const [ya, ma, da] = a.split('-').map(Number)
  const [yb, mb, db] = b.split('-').map(Number)
  const msMotNgay = 86_400_000
  return Math.round((Date.UTC(yb, mb - 1, db) - Date.UTC(ya, ma - 1, da)) / msMotNgay)
}

/**
 * Số TUẦN ISO của một ngày — nhãn "T.37" ở hàng tiêu đề mức Tuần.
 *
 * Theo ISO-8601 chứ không đếm từ 01/01: tuần bắt đầu thứ Hai, và tuần số 1 là
 * tuần chứa thứ Năm đầu tiên của năm. Đếm ngây thơ thì ngày 01/01 rơi vào Chủ
 * nhật sẽ ra "tuần 1" trong khi lịch của cả công ty gọi nó là tuần 52 năm trước.
 */
export function isoWeek(iso: string): number {
  const [y, m, d] = iso.split('-').map(Number)
  const date = new Date(Date.UTC(y, m - 1, d))
  //  Dời tới thứ Năm của cùng tuần: mọi ngày trong tuần khi đó cho cùng một số.
  date.setUTCDate(date.getUTCDate() + 4 - (date.getUTCDay() || 7))
  const dauNam = Date.UTC(date.getUTCFullYear(), 0, 1)
  return Math.ceil(((date.getTime() - dauNam) / 86_400_000 + 1) / 7)
}

export interface GanttTimeline {
  /** Ngày đầu và ngày cuối của dải (đã đệm hai bên và bo theo mức phóng). */
  start: string
  end: string
  /** Mỗi phần tử là MỘT ngày trong dải, theo thứ tự. */
  days: string[]
  dayWidth: number
  totalWidth: number
}

/** Đệm hai bên cho thanh không dính mép. */
const PAD_DAYS = 3

/**
 * KHUNG TỐI THIỂU của trục: **mồng 1 tháng 1 năm nay → 31/12 năm sau**.
 *
 * Đây là đúng cách Lark làm (khách đối chiếu 31/08/2026: tạo một dự án trống
 * tinh, mở Gantt lên là trục đã sẵn hai năm). Bản trước bám sát dữ liệu — mốc
 * sớm nhất trừ 3 ngày tới mốc muộn nhất cộng 3 ngày, sàn 21 ngày — nghe thì gọn
 * nhưng hỏng đúng việc người ta mở Gantt để làm: **đặt lịch cho quãng chưa có
 * việc nào**. Muốn kéo một việc sang quý sau thì quý sau phải nhìn thấy đã, mà
 * dải bám dữ liệu thì chỗ ấy không tồn tại — thành ra phải tạo việc bừa ở đó
 * trước rồi mới kéo được, tức là làm ngược.
 *
 * Sàn 21 ngày cũ bỏ luôn: khung này đã ≥ 730 ngày nên nó không còn chạm tới.
 */
function khungToiThieu(homNay: string): [string, string] {
  const nam = Number(homNay.slice(0, 4))
  return [`${nam}-01-01`, `${nam + 1}-12-31`]
}

/**
 * Dải thời gian: **hợp** của khung tối thiểu hai năm và mọi việc CÓ NGÀY.
 *
 * Vẫn phải nới theo dữ liệu chứ không đóng cứng hai năm: một việc có hạn 2029
 * mà trục dừng ở 2027 thì nó biến mất khỏi biểu đồ — mất việc còn tệ hơn trục
 * dài. Hôm nay luôn nằm trong dải (nó là mốc đọc chính), và điều đó tự đúng vì
 * khung tối thiểu bắt đầu từ đầu năm nay.
 *
 * Hai đầu dải được BO THEO MỨC PHÓNG (`snapEdges`): mức Tuần bo về thứ Hai —
 * Chủ nhật, mức Tháng bo về mồng 1 — ngày cuối tháng. Không bo thì ô đầu và ô
 * cuối của hàng tiêu đề là một tuần/tháng CỤT, hẹp hơn hẳn các ô khác, nhìn như
 * lưới bị vỡ.
 */
export function buildTimeline(
  tasks: WorkTask[],
  zoom: GanttZoom,
  homNay: string = today(),
): GanttTimeline {
  const [sanTruoc, sanSau] = khungToiThieu(homNay)

  //  Đệm 3 ngày CHỈ áp cho mốc của dữ liệu, không áp cho khung tối thiểu: khung
  //  ấy cố ý rơi đúng 01/01 và 31/12, cộng trừ vào là hai đầu trục thành một
  //  tháng cụt ở mức phóng Tháng.
  const moc: string[] = [sanTruoc, sanSau]
  for (const t of tasks) {
    if (t.start_date) moc.push(shiftDate(t.start_date, -PAD_DAYS))
    if (t.due_date) moc.push(shiftDate(t.due_date, PAD_DAYS))
  }
  moc.sort()

  let [start, end] = [moc[0], moc[moc.length - 1]]
  ;[start, end] = snapEdges(start, end, zoom)

  const days: string[] = []
  for (let i = 0; i <= daysBetween(start, end); i += 1) days.push(shiftDate(start, i))

  const dayWidth = DAY_WIDTH[zoom]
  return { start, end, days, dayWidth, totalWidth: days.length * dayWidth }
}

/**
 * Ngày THỨ HAI của tuần chứa `d`. Dùng làm khóa gom ô tuần: một chuỗi ngày là
 * đủ để phân biệt mọi tuần, khỏi phải ghép năm với số tuần — mà ghép hai thứ ấy
 * chính là chỗ đẻ ra lỗi tuần cụt ở giao thừa.
 */
function thuHaiCuaTuan(d: string): string {
  return shiftDate(d, -((weekday(d) + 6) % 7))
}

function snapEdges(start: string, end: string, zoom: GanttZoom): [string, string] {
  if (zoom === 'week') {
    //  Lùi về thứ Hai: `(thu + 6) % 7` biến Chủ nhật (0) thành 6 ngày phải lùi.
    const lui = (weekday(start) + 6) % 7
    const tien = (7 - ((weekday(end) + 6) % 7) - 1) % 7
    return [shiftDate(start, -lui), shiftDate(end, tien)]
  }
  if (zoom === 'month') {
    const [ye, me] = end.split('-').map(Number)
    //  `new Date(y, m, 0)` = ngày 0 của tháng SAU = ngày CUỐI của tháng này (chỉ
    //  số tháng của `Date` đếm từ 0 nên `me` đã là "tháng sau"). Khỏi tra bảng
    //  30/31 và tự đúng cả tháng 2 năm nhuận.
    return [`${start.slice(0, 7)}-01`, toIso(new Date(ye, me, 0))]
  }
  return [start, end]
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
  return rangeGeometry(task.start_date || task.due_date, task.due_date || task.start_date, timeline)
}

/** Hình học của một quãng ngày bất kỳ — dùng cho cả thanh việc lẫn thanh NHÓM. */
export function rangeGeometry(
  from: string,
  to: string,
  timeline: GanttTimeline,
): GanttBar | null {
  if (!from || !to) return null

  //  Ngày bắt đầu sau hạn (dữ liệu nhập ngược) thì đảo lại cho thanh vẫn vẽ được
  //  thay vì ra bề rộng âm và biến mất.
  const tu = from <= to ? from : to
  const den = from <= to ? to : from

  const left = daysBetween(timeline.start, tu) * timeline.dayWidth
  const width = (daysBetween(tu, den) + 1) * timeline.dayWidth
  return { left, width }
}

/** Việc này là CỘT MỐC (B-14) — vẽ hình thoi thay vì thanh. */
export function isMilestone(task: WorkTask): boolean {
  return task.kind === WORK_TASK_KIND.MILESTONE
}

/**
 * Tâm hình thoi của một cột mốc, tính bằng px từ mép trái dải. `null` = mốc
 * chưa có ngày nào.
 */
export function milestoneCenter(task: WorkTask, timeline: GanttTimeline): number | null {
  const ngay = task.due_date || task.start_date
  if (!ngay) return null
  return (daysBetween(timeline.start, ngay) + 0.5) * timeline.dayWidth
}

/** Vị trí VẠCH HÔM NAY (px). `null` = hôm nay nằm ngoài dải, không vẽ vạch. */
export function todayLeft(timeline: GanttTimeline, homNay: string = today()): number | null {
  if (homNay < timeline.start || homNay > timeline.end) return null
  return (daysBetween(timeline.start, homNay) + 0.5) * timeline.dayWidth
}

export interface GanttHeaderCell {
  key: string
  label: string
  /** Bề rộng (px) — ô đầu/cuối có thể ngắn hơn ở mức Ngày, nơi dải không bo. */
  width: number
  /** Dòng phụ trong ô (thứ trong tuần) — chỉ có ở mức Ngày. */
  sub?: string
  /** Ô chứa HÔM NAY — hàng tiêu đề tô đậm nó. */
  isNow?: boolean
}

export interface GanttHeader {
  /** Hàng TRÊN: tháng (mức Ngày) hoặc năm (mức Tuần/Tháng). */
  top: GanttHeaderCell[]
  /** Hàng DƯỚI: ngày · tuần · tháng. Cũng là bộ ô vẽ LƯỚI NỀN. */
  bottom: GanttHeaderCell[]
}

/**
 * Hai hàng tiêu đề của trục thời gian, theo mức phóng — đúng lối Lark:
 *
 * | Mức   | Hàng trên | Hàng dưới          |
 * | ----- | --------- | ------------------ |
 * | Ngày  | Tháng 9/2026 | `28` + `T6`     |
 * | Tuần  | 2026      | `T.37` (tuần ISO)  |
 * | Tháng | 2026      | `Th 9`             |
 *
 * Mức Tuần gom hàng trên theo NĂM chứ không theo tháng: một tuần vắt qua hai
 * tháng, gom theo tháng thì ô tuần bị cắt đôi và hai hàng tiêu đề không còn
 * thẳng mép nhau.
 *
 * `bottom` cũng là bộ ô để vẽ lưới nền — mức Tháng có cả nghìn ngày, vẽ mỗi ngày
 * một `<div>` là hàng nghìn nút DOM cho một tấm lưới không ai nhìn thấy vạch.
 */
export function buildHeader(
  timeline: GanttTimeline,
  zoom: GanttZoom,
  homNay: string = today(),
): GanttHeader {
  if (zoom === 'day') {
    return {
      top: groupCells(timeline, (d) => d.slice(0, 7), monthLabel),
      bottom: timeline.days.map((d) => ({
        key: d,
        label: `${Number(d.slice(8))}`,
        sub: THU[weekday(d)],
        width: timeline.dayWidth,
        isNow: d === homNay,
      })),
    }
  }

  if (zoom === 'week') {
    return {
      top: groupCells(timeline, (d) => d.slice(0, 4), (key) => key),
      //  Khóa ô tuần là NGÀY THỨ HAI của tuần ấy, không phải `năm-tuần`.
      //
      //  ⚠️ Bản cũ ghép năm DƯƠNG LỊCH với số tuần ISO (`2026-w1`), mà hai thứ
      //  đó lệch nhau đúng ở giao thừa: tuần 29/12/2025 → 04/01/2026 là ISO tuần
      //  1 của 2026, nhưng ba ngày đầu mang năm 2025 nên ăn khóa `2025-w1`, bốn
      //  ngày sau ăn `2026-w1` — một tuần bị xẻ thành hai ô cụt 3 và 4 ngày.
      //  Lỗi này có sẵn từ lâu, chỉ chưa ai chạm vì dải cũ ngắn và hiếm khi vắt
      //  qua giao thừa; đổi sang khung hai năm là lộ ngay.
      bottom: groupCells(timeline, thuHaiCuaTuan, (key) => `T.${isoWeek(key)}`, homNay),
    }
  }

  return {
    top: groupCells(timeline, (d) => d.slice(0, 4), (key) => key),
    bottom: groupCells(
      timeline,
      (d) => d.slice(0, 7),
      (key) => `Th ${Number(key.slice(5))}`,
      homNay,
    ),
  }
}

/**
 * Gom các ngày liên tiếp cùng khóa thành một ô.
 *
 * Đi TUẦN TỰ chứ không dùng `Map`: khóa tuần ISO lặp lại ở đầu và cuối một dải
 * dài (tuần 1 của hai năm khác nhau vẫn khác khóa, nhưng dải nhiều năm thì tháng
 * `-01` lặp) — gom bằng `Map` là hai quãng cách nhau cả năm dính vào một ô rộng
 * bằng cả biểu đồ.
 */
function groupCells(
  timeline: GanttTimeline,
  keyOf: (iso: string) => string,
  labelOf: (key: string) => string,
  homNay?: string,
): GanttHeaderCell[] {
  const cells: GanttHeaderCell[] = []
  for (const ngay of timeline.days) {
    const key = keyOf(ngay)
    const last = cells[cells.length - 1]
    if (last && last.key === key) {
      last.width += timeline.dayWidth
      if (homNay && ngay === homNay) last.isNow = true
      continue
    }
    cells.push({
      key,
      label: labelOf(key),
      width: timeline.dayWidth,
      isNow: homNay ? ngay === homNay : undefined,
    })
  }
  return cells
}

function monthLabel(key: string): string {
  return `Tháng ${Number(key.slice(5))}/${key.slice(0, 4)}`
}

/** Cuối tuần tô nhạt cho dễ đọc dải ngày — chỉ có nghĩa ở mức Ngày. */
export function isWeekend(iso: string): boolean {
  const thu = weekday(iso)
  return thu === 0 || thu === 6
}
