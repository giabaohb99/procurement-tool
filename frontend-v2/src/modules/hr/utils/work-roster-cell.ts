import { WORK_DAY_KIND_CODE } from '../types/work-schedule'
import type { WorkRosterCell, WorkRosterItem } from '../types/work-roster'

/**
 * Đọc MỘT ô của lưới «Xem lịch» thành thứ vẽ được. Thuần, không dính React.
 *
 * Trạng thái (từ trên xuống, cái đầu khớp thắng):
 * · `unknown`  — backend không trả ô cho ngày này (hoặc `work_kind` lạ): không đếm, không tô;
 * · `holiday`  — ngày lễ của pháp nhân người đó;
 * · `off`      — lịch hiệu lực ngày đó là nghỉ (Chủ nhật, nghỉ tuần…);
 * · `leave`    — đơn nghỉ phủ HẾT buổi phải đi làm;
 * · `partial`  — đơn nghỉ phủ một nửa, nửa còn lại vẫn đi làm;
 * · `working`  — đi làm bình thường.
 *
 * ⚠️ Đơn nghỉ chỉ có nghĩa khi nó rơi vào buổi PHẢI đi làm. Ngày lễ / ngày nghỉ
 * tuần thì đơn nghỉ không đổi gì (không ai trừ phép ngày đó) nên ô giữ nguyên là
 * Lễ / Nghỉ tuần; ngày làm buổi sáng mà đơn chỉ phủ buổi chiều thì vẫn là đi làm.
 */
export type WorkRosterCellState = 'unknown' | 'holiday' | 'off' | 'leave' | 'partial' | 'working'

export interface WorkRosterCellView {
  state: WorkRosterCellState
  /** Chữ ngắn trong ô tuần («08:00 – 17:00», «Sáng», «Nghỉ», «Lễ», tên loại phép). */
  shortLabel: string
  /** Ký tự cho ô tháng; rỗng = ô để trống (ngày thường, nghỉ lịch, lễ — để ngoại lệ nổi lên). */
  glyph: string
  /** Câu đầy đủ cho tooltip / trình đọc màn hình. */
  description: string
  /** Buổi sáng / chiều ĐANG nghỉ vì đơn (để tô nửa ô). Chỉ khác `false` ở `leave` / `partial`. */
  morningOff: boolean
  afternoonOff: boolean
  /** Có đơn nghỉ làm ô đổi màu → ô bấm được sang đơn. */
  leaveRequestId: number | null
  /** Đơn nghỉ đang chờ duyệt (viền nét đứt). */
  isPending: boolean
  /** Ngày này người đó CÓ đi làm (kể cả nửa buổi) — dùng cho hàng tổng và danh sách điện thoại. */
  isWorking: boolean
}

/**
 * "8:00" / "08:00:00" → "08:00"; giá trị hỏng / rỗng → "".
 * Luôn đủ giờ:phút — bản cũ rút «08:00» thành «08» và ô đọc ra «08–17», đại ca chê (05/10/2026).
 */
export function formatHour(time: string | null | undefined): string {
  const match = /^(\d{1,2}):(\d{2})/.exec(time ?? '')
  return match ? `${match[1].padStart(2, '0')}:${match[2]}` : ''
}

/** Buổi làm theo lịch: [sáng, chiều]. */
function scheduledHalves(workKind: number): [boolean, boolean] | null {
  switch (workKind) {
    case WORK_DAY_KIND_CODE.FULL:
      return [true, true]
    case WORK_DAY_KIND_CODE.MORNING:
      return [true, false]
    case WORK_DAY_KIND_CODE.AFTERNOON:
      return [false, true]
    case WORK_DAY_KIND_CODE.OFF:
      return [false, false]
    default:
      return null
  }
}

const UNKNOWN_VIEW: WorkRosterCellView = {
  state: 'unknown',
  shortLabel: '',
  glyph: '?',
  description: 'Chưa có dữ liệu',
  morningOff: false,
  afternoonOff: false,
  leaveRequestId: null,
  isPending: false,
  isWorking: false,
}

function timeRange(cell: WorkRosterCell): string {
  const start = formatHour(cell.start_time)
  const end = formatHour(cell.end_time)
  return start && end ? `${start} – ${end}` : ''
}

export function describeRosterCell(cell: WorkRosterCell | undefined): WorkRosterCellView {
  if (!cell) return UNKNOWN_VIEW
  const halves = scheduledHalves(cell.work_kind)
  if (!halves) return UNKNOWN_VIEW

  const base = { morningOff: false, afternoonOff: false, leaveRequestId: null, isPending: false }

  if (cell.is_holiday) {
    return {
      ...base,
      state: 'holiday',
      shortLabel: 'Lễ',
      glyph: '',
      description: cell.holiday_name ? `Ngày lễ: ${cell.holiday_name}` : 'Ngày lễ',
      isWorking: false,
    }
  }

  const [worksMorning, worksAfternoon] = halves
  if (!worksMorning && !worksAfternoon) {
    return {
      ...base,
      state: 'off',
      shortLabel: 'Nghỉ',
      glyph: '',
      description: `Nghỉ theo lịch${cell.schedule_name ? ` «${cell.schedule_name}»` : ''}`,
      isWorking: false,
    }
  }

  const leave = cell.leave
  //  Chỉ tính nửa buổi nghỉ rơi vào buổi PHẢI đi làm.
  const morningOff = Boolean(leave?.morning) && worksMorning
  const afternoonOff = Boolean(leave?.afternoon) && worksAfternoon

  if (leave && (morningOff || afternoonOff)) {
    const status = leave.is_approved ? 'đã duyệt' : 'chờ duyệt'
    const detail = `${leave.leave_type_name} (${status}) · ${leave.code}`
    const remainsMorning = worksMorning && !morningOff
    const remainsAfternoon = worksAfternoon && !afternoonOff
    const common = {
      morningOff,
      afternoonOff,
      leaveRequestId: leave.request_id,
      isPending: !leave.is_approved,
    }

    if (!remainsMorning && !remainsAfternoon) {
      return {
        ...common,
        state: 'leave',
        shortLabel: leave.leave_type_name || 'Nghỉ phép',
        glyph: 'P',
        description: `Nghỉ cả ngày — ${detail}`,
        isWorking: false,
      }
    }
    return {
      ...common,
      state: 'partial',
      //  Nói buổi NGHỈ, không nói buổi làm: «Sáng» trơn đọc ra như lịch chỉ làm buổi sáng
      //  (ô `working` của ngày nửa buổi cũng ghi «Sáng») — hai nghĩa ngược nhau, một chữ.
      shortLabel: morningOff ? 'Nghỉ sáng' : 'Nghỉ chiều',
      glyph: 'P',
      description: `Nghỉ ${morningOff ? 'buổi sáng' : 'buổi chiều'} — ${detail}`,
      isWorking: true,
    }
  }

  let shortLabel = timeRange(cell)
  if (cell.work_kind === WORK_DAY_KIND_CODE.MORNING) shortLabel = 'Sáng'
  else if (cell.work_kind === WORK_DAY_KIND_CODE.AFTERNOON) shortLabel = 'Chiều'
  else if (!shortLabel) shortLabel = 'Làm'

  const hours = timeRange(cell)
  return {
    ...base,
    state: 'working',
    shortLabel,
    glyph: cell.work_kind === WORK_DAY_KIND_CODE.MORNING ? 'S' : cell.work_kind === WORK_DAY_KIND_CODE.AFTERNOON ? 'C' : '',
    description: `Đi làm${hours ? ` ${hours}` : ''}${cell.schedule_name ? ` — ${cell.schedule_name}` : ''}`,
    isWorking: true,
  }
}

/** Gom ô của một nhân sự theo ngày: tra O(1) thay vì `find` trong từng ô của lưới. */
export function indexCellsByDate(item: WorkRosterItem): Map<string, WorkRosterCell> {
  const map = new Map<string, WorkRosterCell>()
  for (const cell of item.cells) map.set(cell.date, cell)
  return map
}
