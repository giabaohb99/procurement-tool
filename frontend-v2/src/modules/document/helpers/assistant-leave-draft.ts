/**
 * Đọc bản nháp ĐƠN NGHỈ PHÉP do Trợ lý AI soạn (tool `draft_leave_request`) thành giá trị
 * điền sẵn cho form tạo văn bản.
 *
 * Args là kết quả tool do MODEL điền nên phải parse phòng thủ: sai kiểu thì bỏ trường đó,
 * thiếu phần cốt lõi (loại văn bản, ngày nghỉ, lý do) thì trả `null` — trang tạo văn bản
 * mở trắng như thường chứ không vỡ. Người dùng rà lại trên form rồi tự bấm Tạo, văn bản
 * KHÔNG tự sinh.
 */

const SESSIONS = new Set(['full', 'morning', 'afternoon'])

export interface AssistantLeaveDraft {
  doc_type_id: number
  title: string
  leave: {
    leave_type: string
    from_date: string
    from_session: string
    to_date: string
    to_session: string
    total_days: number | ''
    reason: string
    contact_phone: string
  }
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

function asSession(value: unknown): string {
  const text = asText(value)
  return SESSIONS.has(text) ? text : 'full'
}

/** `null` nghĩa là state không phải bản nháp nghỉ phép hợp lệ. */
export function parseAssistantLeaveDraft(raw: unknown): AssistantLeaveDraft | null {
  if (typeof raw !== 'object' || raw === null) return null
  const data = raw as Record<string, unknown>
  //  Chốt theo `kind`: cùng một ô `location.state.assistantDraft` còn chở bản nháp
  //  YCBG/YCMH — nhận nhầm là form văn bản điền rác.
  if (data.kind !== 'leave_request') return null

  const docTypeId = typeof data.doc_type_id === 'number' ? Math.trunc(data.doc_type_id) : 0
  const leaveRaw =
    typeof data.leave === 'object' && data.leave !== null
      ? (data.leave as Record<string, unknown>)
      : {}
  const fromDate = asText(leaveRaw.from_date)
  const toDate = asText(leaveRaw.to_date)
  const reason = asText(leaveRaw.reason)
  if (docTypeId <= 0 || !fromDate || !toDate || !reason) return null

  const totalDays =
    typeof leaveRaw.total_days === 'number' && leaveRaw.total_days > 0 ? leaveRaw.total_days : ''

  return {
    doc_type_id: docTypeId,
    title: asText(data.title),
    leave: {
      leave_type: asText(leaveRaw.leave_type) || 'annual',
      from_date: fromDate,
      from_session: asSession(leaveRaw.from_session),
      to_date: toDate,
      to_session: asSession(leaveRaw.to_session),
      total_days: totalDays,
      reason,
      contact_phone: asText(leaveRaw.contact_phone),
    },
  }
}
