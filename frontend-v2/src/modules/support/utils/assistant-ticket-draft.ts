/**
 * Đọc bản nháp PHIẾU HỖ TRỢ do Trợ lý AI soạn (tool `ticket_create`, CR-218) thành giá
 * trị mở sẵn cho dialog tạo phiếu ở `/support`.
 *
 * Args là kết quả tool do MODEL điền nên phải parse phòng thủ: sai kiểu thì bỏ trường đó,
 * thiếu phần cốt lõi (chủ đề, nội dung) thì trả `null` — trang mở như thường chứ không vỡ.
 * Người dùng rà lại trong dialog rồi tự bấm Gửi, phiếu KHÔNG tự sinh.
 */

import { TICKET_PRIORITY_LABELS } from '../config/ticket-constants'

export interface AssistantTicketDraft {
  subject: string
  department: string
  priority: string
  body: string
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

/** `null` nghĩa là state không phải bản nháp phiếu hỗ trợ hợp lệ. */
export function parseAssistantTicketDraft(raw: unknown): AssistantTicketDraft | null {
  if (typeof raw !== 'object' || raw === null) return null
  const data = raw as Record<string, unknown>
  //  Chốt theo `kind`: cùng khuôn bản nháp trợ lý với YCBG/YCMH/nghỉ phép — nhận nhầm
  //  loại khác là dialog điền rác.
  if (data.kind !== 'ticket') return null

  const subject = asText(data.subject)
  const body = asText(data.body)
  if (!subject || !body) return null

  const priority = asText(data.priority)
  return {
    subject,
    //  Bộ phận backend đã ép về danh sách hợp lệ; dialog tự giữ mặc định nếu rỗng/lạ.
    department: asText(data.department),
    priority: priority in TICKET_PRIORITY_LABELS ? priority : 'normal',
    body,
  }
}
