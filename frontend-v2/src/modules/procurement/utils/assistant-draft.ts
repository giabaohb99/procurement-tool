/**
 * Đọc bản nháp YCBG do Trợ lý AI soạn (args của tool `draft_survey_request`) thành dữ liệu
 * điền sẵn cho form tạo phiếu.
 *
 * Args là do MODEL điền nên phải parse phòng thủ: sai kiểu thì bỏ qua trường đó chứ không
 * làm vỡ trang. Trang tạo YCBG nhận bản nháp qua `location.state.assistantDraft` — người
 * dùng rà lại rồi tự bấm Tạo, phiếu KHÔNG tự sinh.
 */

export interface AssistantDraftLine {
  requirement_detail: string
  item_group: string
  request_qty: number
  uom: string
  proposed_price: number
  other_requirement: string
}

export interface AssistantDraft {
  purpose: string
  note: string
  lines: AssistantDraftLine[]
}

function asText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

function asQty(value: unknown): number {
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) && n >= 0 ? n : 0
}

/** `null` nghĩa là state không phải bản nháp hợp lệ (thiếu mục đích hoặc không có dòng nào). */
export function parseAssistantDraft(raw: unknown): AssistantDraft | null {
  if (typeof raw !== 'object' || raw === null) return null
  const data = raw as Record<string, unknown>

  const purpose = asText(data.purpose)
  const rawLines = Array.isArray(data.lines) ? data.lines : []
  const lines: AssistantDraftLine[] = []
  for (const item of rawLines) {
    if (typeof item !== 'object' || item === null) continue
    const line = item as Record<string, unknown>
    const detail = asText(line.requirement_detail)
    if (!detail) continue
    lines.push({
      requirement_detail: detail,
      item_group: asText(line.item_group),
      request_qty: asQty(line.request_qty),
      uom: asText(line.uom),
      proposed_price: asQty(line.proposed_price),
      other_requirement: asText(line.other_requirement),
    })
  }

  if (!purpose || lines.length === 0) return null
  return { purpose, note: asText(data.note), lines }
}
