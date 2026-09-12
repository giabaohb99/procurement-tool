/**
 * Đọc bản nháp ĐƠN NGHỈ PHÉP do Trợ lý AI soạn (tool `draft_leave_request`) thành giá trị
 * điền sẵn cho form `/hr/leave-requests/new`.
 *
 * ⚠️ Bản trước của tệp này nằm ở `modules/document/helpers/` và điền vào form tạo VĂN BẢN
 * (giấy GNP ở Văn thư) — sai phân hệ, xem bao-CR-387. Giấy GNP do hệ tự sinh sau khi đơn
 * được duyệt; chỗ người dùng nộp đơn là phân hệ Nghỉ phép.
 *
 * Args là kết quả tool do MODEL điền nên phải parse phòng thủ: sai kiểu thì bỏ trường đó,
 * thiếu phần cốt lõi (ngày nghỉ, lý do, loại nghỉ) thì trả `null` — trang mở form trắng
 * như thường chứ không vỡ. Người dùng rà lại rồi tự bấm Lưu, đơn KHÔNG tự sinh.
 */
import { LEAVE_SESSION } from '../types/leave'
import { REASON_MAX, type LeaveFormValues } from './leave-form-values'

//  Bộ buổi nghỉ hợp lệ, lấy thẳng từ bộ mã dùng chung để đổi một chỗ là cả hai bên theo.
const SESSIONS: number[] = Object.values(LEAVE_SESSION)

export interface AssistantLeaveDraft {
  leave_type_id: number
  days: number
  from_date: string
  to_date: string
  from_session: number
  to_session: number
  from_time: string
  to_time: string
  reason: string
  contact_phone: string
}

function asText(value: unknown, limit: number): string {
  return typeof value === 'string' ? value.trim().slice(0, limit) : ''
}

/**
 * `YYYY-MM-DD` mới nhận — chuỗi khác dạng vào ô ngày là ô đó hỏng im lặng.
 *
 * ⚠️ Kiểm regex trên chuỗi ĐẦY ĐỦ, đừng cắt 10 ký tự trước rồi mới kiểm: làm vậy
 * thì `2026-09-011` (gõ thừa một số) bị cắt thành một ngày HỢP LỆ nhưng KHÁC,
 * và form điền sẵn một ngày không ai gõ.
 */
function asDate(value: unknown): string {
  const text = typeof value === 'string' ? value.trim() : ''
  return /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : ''
}

/** Cùng lý do với `asDate`: kiểm nguyên chuỗi, không cắt trước. */
function asTime(value: unknown): string {
  const text = typeof value === 'string' ? value.trim() : ''
  return /^\d{2}:\d{2}$/.test(text) ? text : ''
}

function asSession(value: unknown): number {
  return typeof value === 'number' && SESSIONS.includes(value) ? value : LEAVE_SESSION.FULL
}

/** `null` nghĩa là state không phải bản nháp đơn nghỉ phép hợp lệ. */
export function parseAssistantLeaveDraft(raw: unknown): AssistantLeaveDraft | null {
  if (typeof raw !== 'object' || raw === null) return null
  const data = raw as Record<string, unknown>
  //  Chốt theo `kind`: cùng một ô `location.state.assistantDraft` còn chở bản nháp
  //  YCBG/YCMH — nhận nhầm là form điền rác.
  if (data.kind !== 'leave_request') return null

  const fromDate = asDate(data.from_date)
  const toDate = asDate(data.to_date)
  const reason = asText(data.reason, REASON_MAX)
  //  Dòng loại nghỉ nằm trong mảng `lines` (hình dạng chừa chỗ cho đơn nhiều loại sau
  //  này); đợt này tool luôn soạn đúng một dòng.
  const line = Array.isArray(data.lines) && data.lines.length > 0 ? data.lines[0] : null
  const lineData = typeof line === 'object' && line !== null ? (line as Record<string, unknown>) : {}
  const leaveTypeId =
    typeof lineData.leave_type_id === 'number' ? Math.trunc(lineData.leave_type_id) : 0
  if (!fromDate || !toDate || !reason || leaveTypeId <= 0) return null

  const days = typeof lineData.days === 'number' && lineData.days > 0 ? lineData.days : 0
  const fromSession = asSession(data.from_session)
  const toSession = asSession(data.to_session)
  const hourly = fromSession === LEAVE_SESSION.HOURLY || toSession === LEAVE_SESSION.HOURLY

  return {
    leave_type_id: leaveTypeId,
    days,
    from_date: fromDate,
    to_date: toDate,
    from_session: fromSession,
    to_session: toSession,
    //  Giờ chỉ có nghĩa khi nghỉ theo giờ; giữ lại ở ca khác là form gửi kèm hai ô thừa.
    from_time: hourly ? asTime(data.from_time) : '',
    to_time: hourly ? asTime(data.to_time) : '',
    reason,
    contact_phone: asText(data.contact_phone, 30),
  }
}

/** Đè bản nháp lên form rỗng. Giữ nguyên mọi ô nháp không nói tới (người nghỉ, bàn giao...). */
export function applyAssistantLeaveDraft(
  base: LeaveFormValues,
  draft: AssistantLeaveDraft,
): LeaveFormValues {
  return {
    ...base,
    from_date: draft.from_date,
    to_date: draft.to_date,
    from_session: draft.from_session,
    to_session: draft.to_session,
    from_time: draft.from_time,
    to_time: draft.to_time,
    reason: draft.reason,
    contact_phone: draft.contact_phone || base.contact_phone,
    lines: [{ leave_type_id: draft.leave_type_id, days: draft.days }],
  }
}
