import type { ChatReply } from '../types/assistant'

/** Loại phiếu trợ lý soạn nháp được — khớp bộ tool `draft_*` của backend. */
export type DraftTarget = 'survey' | 'purchase' | 'leave'

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

/** Lấy file báo cáo trợ lý vừa xuất (tool `export_report_file`) từ lượt trả lời. */
export function pickFileOffer(reply: ChatReply): FileOffer | null {
  const call = (reply.tool_calls ?? [])
    .filter((c) => c.name === 'export_report_file' && c.file != null)
    .at(-1)
  if (!call?.file) return null
  return {
    conversationId: reply.conversation_id,
    filename: call.file.filename,
    downloadUrl: call.file.download_url,
  }
}
