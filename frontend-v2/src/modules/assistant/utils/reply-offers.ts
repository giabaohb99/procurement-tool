import type { ChatReply, UpdateProposal } from '../types/assistant'

/** Loại phiếu trợ lý soạn nháp được — khớp bộ tool `draft_*` + `ticket_create` của backend. */
export type DraftTarget = 'survey' | 'purchase' | 'leave' | 'payment' | 'ticket'

/** Bản nháp trợ lý vừa soạn — chỉ sống trong lượt trả lời hiện tại, backend không lưu. */
export interface DraftOffer {
  conversationId: number
  args: Record<string, unknown>
  target: DraftTarget
}

/** File báo cáo trợ lý vừa xuất — file ĐÃ nằm trên máy chủ, nút chỉ tải về. */
export interface FileOffer {
  conversationId: number
  filename: string
  downloadUrl: string
}

const DRAFT_TARGETS: Record<string, DraftTarget> = {
  draft_survey_request: 'survey',
  draft_purchase_request: 'purchase',
  draft_leave_request: 'leave',
  draft_payment_request: 'payment',
  ticket_create: 'ticket',
}

/**
 * Lấy bản nháp trợ lý vừa soạn từ lượt trả lời (`rows > 0` = tool chạy thành công,
 * không bị chặn quyền). Lượt không soạn gì trả null để GỠ nút của lượt trước.
 */
export function pickDraftOffer(reply: ChatReply): DraftOffer | null {
  const call = (reply.tool_calls ?? [])
    .filter((c) => DRAFT_TARGETS[c.name] != null && c.rows != null && c.rows > 0)
    .at(-1)
  if (!call) return null
  return {
    conversationId: reply.conversation_id,
    //  Ưu tiên bản draft ĐÃ CHUẨN HÓA từ kết quả tool (ĐVT/mã hàng khớp chính tả
    //  danh mục); args thô do model gõ chỉ là dự phòng.
    args: call.draft ?? call.args,
    target: DRAFT_TARGETS[call.name],
  }
}

/** Đề xuất sửa phiếu (CR-218) — cũng chỉ sống trong lượt trả lời hiện tại. */
export interface UpdateOffer {
  conversationId: number
  proposal: UpdateProposal
}

/**
 * Lấy đề xuất sửa phiếu từ lượt trả lời — chỉ tool `propose_document_update` có khối
 * `proposal`. Lượt không đề xuất gì trả null để gỡ thẻ xác nhận của lượt trước
 * (token cũ vẫn tự hết hạn ở backend, nhưng thẻ hiện dai sẽ gây bấm nhầm).
 */
export function pickUpdateOffer(reply: ChatReply): UpdateOffer | null {
  const call = (reply.tool_calls ?? [])
    .filter((c) => c.name === 'propose_document_update' && c.proposal != null)
    .at(-1)
  if (!call?.proposal) return null
  return { conversationId: reply.conversation_id, proposal: call.proposal }
}

/** Bộ tool xuất file của trợ lý — tool nào cũng trả khối `file` cùng hình dạng. */
const EXPORT_TOOLS = new Set(['export_report_file', 'export_excel_file'])

/** Lấy file báo cáo trợ lý vừa xuất (Word hoặc Excel) từ lượt trả lời. */
export function pickFileOffer(reply: ChatReply): FileOffer | null {
  const call = (reply.tool_calls ?? [])
    .filter((c) => EXPORT_TOOLS.has(c.name) && c.file != null)
    .at(-1)
  if (!call?.file) return null
  return {
    conversationId: reply.conversation_id,
    filename: call.file.filename,
    downloadUrl: call.file.download_url,
  }
}
