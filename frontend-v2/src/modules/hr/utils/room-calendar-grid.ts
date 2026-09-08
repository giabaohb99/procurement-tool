import type { RoomBooking } from '../types/room'
import { BLOCKING_ROOM_STATUSES } from '../types/room'

/**
 * Xếp phiếu đặt phòng lên LƯỚI GIỜ — hàm thuần, không đụng React.
 *
 * Lưới của màn lịch là **cột = phòng, hàng = giờ**, đúng cách người ta nhìn một
 * bảng đặt phòng treo ở sảnh: liếc một cột là biết phòng đó cả ngày ra sao. Xếp
 * ngược lại (cột = giờ) thì phải đọc ngang qua nhiều phòng mới trả lời được câu
 * hỏi duy nhất người dùng mang tới đây — *"phòng nào đang trống"*.
 */

/** Giờ mở/đóng của lưới. Ngoài khoảng này gần như không ai họp. */
export const DAY_START_HOUR = 7
export const DAY_END_HOUR = 20
/** Chiều cao một giờ, tính bằng pixel — dùng cả cho thước giờ lẫn khối phiếu. */
export const HOUR_HEIGHT = 56

/**
 * GIỜ HÀNH CHÍNH — dùng để tô mờ phần ngoài giờ.
 *
 * Lưới trắng đều từ 7h tới 20h thì mắt không có mốc nào để bám: 8h sáng và 19h
 * tối trông y hệt nhau, trong khi gần như mọi cuộc họp nằm trong khung hành
 * chính. Tô mờ phần ngoài giờ (và giờ nghỉ trưa) là cách rẻ nhất để nói ra điều
 * đó mà không thêm một dòng chữ nào.
 */
export const WORK_START_HOUR = 8
export const WORK_END_HOUR = 17.5
export const LUNCH_START_HOUR = 12
export const LUNCH_END_HOUR = 13.5

/** Khoảng thời gian mờ (ngoài giờ làm), tính sẵn theo pixel cho tầng vẽ. */
export function dimBands(): { top: number; height: number }[] {
  const px = (hour: number) => (hour - DAY_START_HOUR) * HOUR_HEIGHT
  return [
    { top: 0, height: px(WORK_START_HOUR) },
    { top: px(LUNCH_START_HOUR), height: px(LUNCH_END_HOUR) - px(LUNCH_START_HOUR) },
    { top: px(WORK_END_HOUR), height: px(DAY_END_HOUR) - px(WORK_END_HOUR) },
  ].filter((band) => band.height > 0)
}

/**
 * Vị trí vạch «bây giờ» trên lưới, `null` nếu đang xem ngày khác hoặc giờ hiện
 * tại nằm ngoài khung lưới.
 *
 * Vạch này là mốc neo mắt quan trọng nhất của một màn lịch: không có nó thì
 * người xem phải tự dò xem mình đang ở đâu trong ngày.
 */
export function nowLineTop(day: Date, now: Date): number | null {
  if (day.toDateString() !== now.toDateString()) return null
  const hour = now.getHours() + now.getMinutes() / 60
  if (hour < DAY_START_HOUR || hour > DAY_END_HOUR) return null
  return (hour - DAY_START_HOUR) * HOUR_HEIGHT
}

/**
 * Các ô bấm để đặt — **nửa tiếng một ô**, không phải một tiếng.
 *
 * Họp 30 phút là chuyện thường; ô một tiếng buộc người dùng bấm rồi sửa lại giờ
 * trên form, tức là bấm cho có. Trả về giờ dạng số thập phân (`9.5` = 9:30) để
 * tầng vẽ tự dựng nhãn.
 */
export function halfHourSlots(): number[] {
  const slots: number[] = []
  for (let hour = DAY_START_HOUR; hour < DAY_END_HOUR; hour += 0.5) slots.push(hour)
  return slots
}

/** `9.5` → `09:30`. */
export function formatSlotHour(hour: number): string {
  const h = Math.floor(hour)
  const m = Math.round((hour - h) * 60)
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

export interface BookingBlock {
  booking: RoomBooking
  /** Khoảng cách từ đỉnh lưới, px. */
  top: number
  height: number
  /** Bề rộng theo phần trăm cột và độ lệch trái — dùng khi hai phiếu chồng giờ. */
  widthPercent: number
  leftPercent: number
}

function minutesFromDayStart(value: Date): number {
  return (value.getHours() - DAY_START_HOUR) * 60 + value.getMinutes()
}

/** Phiếu này có nằm trong NGÀY đang xem không (so theo ngày địa phương). */
export function isOnDay(booking: RoomBooking, day: Date): boolean {
  const start = new Date(booking.start_at)
  const end = new Date(booking.end_at)
  const dayStart = new Date(day)
  dayStart.setHours(0, 0, 0, 0)
  const dayEnd = new Date(dayStart)
  dayEnd.setDate(dayEnd.getDate() + 1)
  //  Cuộc họp vắt qua nửa đêm vẫn phải hiện ở CẢ HAI ngày.
  return start < dayEnd && end > dayStart
}

/**
 * Chỉ những phiếu ĐANG GIỮ phòng mới được vẽ như đã chiếm chỗ.
 *
 * ⚠️ Nháp, đã hủy, bị từ chối **không** chiếm chỗ. Vẽ chúng lên lịch là người
 * xem tưởng phòng đã kín rồi đi đặt phòng khác — trong khi phòng đang trống.
 */
export function blockingOnly(bookings: RoomBooking[]): RoomBooking[] {
  return bookings.filter((b) => BLOCKING_ROOM_STATUSES.includes(b.status))
}

/**
 * Dựng khối cho MỘT phòng trong MỘT ngày.
 *
 * Hai phiếu chồng giờ (trạng thái *Chờ duyệt* của hai người khác nhau, hoặc dữ
 * liệu cũ) được xếp **cạnh nhau**, mỗi khối một nửa cột — chồng đè lên nhau thì
 * cái dưới biến mất và người xem không bao giờ biết là có nó.
 */
export function buildDayBlocks(bookings: RoomBooking[], day: Date): BookingBlock[] {
  const rows = blockingOnly(bookings)
    .filter((b) => isOnDay(b, day))
    .sort((a, b) => a.start_at.localeCompare(b.start_at))

  const gridMinutes = (DAY_END_HOUR - DAY_START_HOUR) * 60

  //  Gom thành cụm chồng nhau để biết mỗi khối chiếm bao nhiêu phần bề ngang.
  const clusters: RoomBooking[][] = []
  for (const booking of rows) {
    const last = clusters[clusters.length - 1]
    const overlapsPrevCluster =
      last && last.some((other) => booking.start_at < other.end_at && booking.end_at > other.start_at)
    if (overlapsPrevCluster) last.push(booking)
    else clusters.push([booking])
  }

  return clusters.flatMap((cluster) =>
    cluster.map((booking, index) => {
      const start = new Date(booking.start_at)
      const end = new Date(booking.end_at)
      //  Kẹp vào khung giờ của lưới: họp từ 6h sáng thì vẽ từ mép trên, không
      //  đẩy khối lên trên đỉnh lưới rồi biến mất.
      const from = Math.max(0, minutesFromDayStart(start))
      const to = Math.min(gridMinutes, minutesFromDayStart(end))
      return {
        booking,
        top: (from / 60) * HOUR_HEIGHT,
        //  Sàn 24px: cuộc họp 15 phút mà vẽ đúng tỷ lệ thì không đọc nổi chữ.
        height: Math.max(24, ((to - from) / 60) * HOUR_HEIGHT),
        widthPercent: 100 / cluster.length,
        leftPercent: (100 / cluster.length) * index,
      }
    }),
  )
}

/**
 * ── TRỤC NGANG: mỗi phòng một HÀNG, giờ chạy ngang ──────────────────────────
 *
 * ⚠️ Bản đầu (04/09/2026) lấy **cột làm phòng**. Đẹp với bốn phòng, nhưng khách
 * hỏi đúng câu quyết định: *"20 phòng thì sao?"* — 20 cột × 224px là **4.500px**,
 * tức cuộn ngang bốn màn hình mới xem hết, và không lúc nào thấy toàn cảnh.
 *
 * Đảo trục thì số phòng chỉ làm lưới **dài xuống** — cuộn dọc là thao tác người
 * ta làm sẵn ở mọi trang — còn cả ngày làm việc luôn nằm trọn trong một màn.
 * Đây cũng là cách mọi phần mềm đặt tài nguyên làm khi số tài nguyên lớn.
 */

/**
 * ⚠️ Trục ngang tính bằng **PHẦN TRĂM**, không phải pixel.
 *
 * Bản px (04/09/2026 sáng) khoá lưới ở 13 × 84px: màn 2.289px thì lưới hết ở
 * 19:00 và chừa một nghìn pixel trắng bên phải — khách chụp lại đúng chỗ đó.
 * Tính theo phần trăm thì lưới tự lấp đầy khung, còn khung hẹp đã có
 * `min-width` ở tầng vẽ lo (cuộn ngang).
 */

/** Tổng số phút mà lưới bày ra — mẫu số của mọi phép tính phần trăm. */
export const GRID_MINUTES = (DAY_END_HOUR - DAY_START_HOUR) * 60

/**
 * Chiều cao một hàng phòng, co theo SỐ PHÒNG.
 *
 * Bốn phòng mà hàng vẫn 52px thì lưới cao 210px giữa một khung rỗng 1.100px —
 * ít phòng thì hàng phải dày ra. Hai chục phòng thì ngược lại: hàng mỏng để
 * nhiều phòng lọt vào một màn, phần dư đã có cuộn dọc lo.
 */
export function rowHeightFor(roomCount: number): number {
  if (roomCount <= 4) return 92
  if (roomCount <= 8) return 68
  if (roomCount <= 14) return 56
  return 48
}

export interface BookingBar {
  booking: RoomBooking
  /** Vị trí và bề rộng theo % bề ngang lưới. */
  leftPercent: number
  widthPercent: number
  /** Chồng giờ thì chia đôi chiều cao hàng — xem `buildRowBars`. */
  heightPercent: number
  topPercent: number
}

/**
 * Dựng thanh cho MỘT phòng trong MỘT ngày, trên trục ngang.
 *
 * Hai phiếu chồng giờ xếp **chồng lên nhau theo chiều dọc** trong cùng hàng, mỗi
 * cái một nửa chiều cao — vẽ đè thì cái dưới biến mất và người xem không bao giờ
 * biết là có nó.
 */
export function buildRowBars(bookings: RoomBooking[], day: Date): BookingBar[] {
  const rows = blockingOnly(bookings)
    .filter((b) => isOnDay(b, day))
    .sort((a, b) => a.start_at.localeCompare(b.start_at))

  const clusters: RoomBooking[][] = []
  for (const booking of rows) {
    const last = clusters[clusters.length - 1]
    const overlaps =
      last && last.some((o) => booking.start_at < o.end_at && booking.end_at > o.start_at)
    if (overlaps) last.push(booking)
    else clusters.push([booking])
  }

  return clusters.flatMap((cluster) =>
    cluster.map((booking, index) => {
      const from = Math.max(0, minutesFromDayStart(new Date(booking.start_at)))
      const to = Math.min(GRID_MINUTES, minutesFromDayStart(new Date(booking.end_at)))
      return {
        booking,
        leftPercent: (from / GRID_MINUTES) * 100,
        //  Sàn 1.5%: cuộc họp 15 phút chỉ chiếm 1.9% bề ngang, hẹp tới mức mất
        //  cả viền. Không phải con số đẹp, nhưng nó là ngưỡng đọc được.
        widthPercent: Math.max(1.5, ((to - from) / GRID_MINUTES) * 100),
        heightPercent: 100 / cluster.length,
        topPercent: (100 / cluster.length) * index,
      }
    }),
  )
}

/** Vùng mờ ngoài giờ làm, tính theo % trục NGANG. */
export function dimBandsX(): { leftPercent: number; widthPercent: number }[] {
  const pct = (hour: number) => ((hour - DAY_START_HOUR) * 60 / GRID_MINUTES) * 100
  return [
    { leftPercent: 0, widthPercent: pct(WORK_START_HOUR) },
    {
      leftPercent: pct(LUNCH_START_HOUR),
      widthPercent: pct(LUNCH_END_HOUR) - pct(LUNCH_START_HOUR),
    },
    { leftPercent: pct(WORK_END_HOUR), widthPercent: 100 - pct(WORK_END_HOUR) },
  ].filter((band) => band.widthPercent > 0)
}

/** Vị trí vạch «bây giờ» theo % trục NGANG, `null` nếu không phải hôm nay. */
export function nowLineLeft(day: Date, now: Date): number | null {
  const top = nowLineTop(day, now)
  if (top === null) return null
  return (top / ((DAY_END_HOUR - DAY_START_HOUR) * HOUR_HEIGHT)) * 100
}

/** Vị trí một mốc giờ theo % — dùng cho thước giờ và ô bấm. */
export function hourPercent(hour: number): number {
  return (((hour - DAY_START_HOUR) * 60) / GRID_MINUTES) * 100
}

/** Nhãn thước giờ bên trái lưới: 7:00 → 20:00. */
export function hourLabels(): string[] {
  const labels: string[] = []
  for (let hour = DAY_START_HOUR; hour <= DAY_END_HOUR; hour += 1) {
    labels.push(`${String(hour).padStart(2, '0')}:00`)
  }
  return labels
}
