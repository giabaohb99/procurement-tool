import type {
  SurveyRequestFromPurchaseRequest,
  SurveyRequestLineFromPurchaseRequest,
} from './purchase-request-survey-request-prefill'
import type { SurveyRequestDetail, SurveyRequestLine } from '../types/survey-request-detail'
import { EMPTY_SURVEY_REQUEST_LINE } from './survey-request-lines-table'

/**
 * Gói `location.state.fromPr` đọc được ở màn TẠO YCBG — khuôn của nút *Tạo yêu cầu báo giá*
 * trên YCMH bị trả lại / từ chối (CR-026, dời sang v2 ở duoc-CR-741). Thêm `handler_dept_id`
 * tùy chọn vì bản v1 cũng đọc trường đó (YCMH nguồn đã nhờ phòng khác xử lý thì giữ phòng ấy).
 */
export type SurveyRequestFromPurchaseRequestState = SurveyRequestFromPurchaseRequest & {
  handler_dept_id: number
  department_id: number
  head_of_dept_id: number
}

/** Dòng YCBG điền sẵn — giữ `src_pr_item_id` để backend kéo ảnh của dòng YCMH nguồn khi Lưu. */
export type SurveyRequestLineWithSource = SurveyRequestLine & { src_pr_item_id: number }

function asText(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function asNumber(value: unknown): number {
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) && n > 0 ? n : 0
}

function parseLine(raw: unknown): SurveyRequestLineFromPurchaseRequest | null {
  if (typeof raw !== 'object' || raw === null) return null
  const line = raw as Record<string, unknown>
  return {
    received_date: asText(line.received_date),
    result_due_date: asText(line.result_due_date),
    item_group: asText(line.item_group),
    requirement_detail: asText(line.requirement_detail),
    other_requirement: asText(line.other_requirement),
    request_qty: asNumber(line.request_qty),
    uom: asText(line.uom),
    proposed_price: asNumber(line.proposed_price),
    src_pr_item_id: asNumber(line.src_pr_item_id),
  }
}

/**
 * Đọc phòng thủ `state.fromPr` — state đi qua lịch sử trình duyệt nên có thể là bất cứ thứ gì
 * (trang mở lại sau khi cập nhật bản mới, người dùng tự gõ). Không có mã YCMH nguồn thì coi
 * như không có gói, để màn khỏi hiện nhãn "Từ " trống.
 */
export function parseSurveyRequestFromPurchaseRequest(
  raw: unknown,
): SurveyRequestFromPurchaseRequestState | null {
  if (typeof raw !== 'object' || raw === null) return null
  const data = raw as Record<string, unknown>
  const prCode = asText(data.pr_code).trim()
  if (!prCode) return null
  const lines = (Array.isArray(data.lines) ? data.lines : [])
    .map(parseLine)
    .filter((line): line is SurveyRequestLineFromPurchaseRequest => line !== null)
  return {
    pr_id: asNumber(data.pr_id),
    pr_code: prCode,
    company_id: asNumber(data.company_id),
    handler_dept_id: asNumber(data.handler_dept_id),
    requester: asText(data.requester),
    requester_id: asNumber(data.requester_id),
    requester_position: asText(data.requester_position),
    department: asText(data.department),
    department_id: asNumber(data.department_id),
    head_of_dept: asText(data.head_of_dept),
    head_of_dept_id: asNumber(data.head_of_dept_id),
    purpose: asText(data.purpose),
    note: asText(data.note),
    lines,
  }
}

/**
 * Điền phiếu YCBG rỗng từ YCMH nguồn — đúng các trường bản v1 điền (`SurveyRequestDetail.tsx`
 * khởi tạo `sv`): công ty, phòng xử lý, người yêu cầu + chức vụ, phòng ban, trưởng bộ phận,
 * mục đích, ghi chú kèm vết "(Tạo từ YCMH <mã>)", và các dòng (giữ `src_pr_item_id`).
 * Trường nào YCMH nguồn để trống thì giữ giá trị mặc định của phiếu rỗng như v1 dùng `|| ''`
 * — riêng công ty: v1 về 0, ở đây giữ công ty của người lập để ô chọn không trống.
 */
export function applySurveyRequestFromPurchaseRequest(
  base: SurveyRequestDetail,
  fromPr: SurveyRequestFromPurchaseRequestState,
): SurveyRequestDetail {
  const lines: SurveyRequestLineWithSource[] = fromPr.lines.map((line) => ({
    ...EMPTY_SURVEY_REQUEST_LINE,
    ...line,
  }))
  return {
    ...base,
    company_id: fromPr.company_id || base.company_id,
    handler_dept_id: fromPr.handler_dept_id,
    //  YCMH nguồn đã có phòng xử lý thì coi như đã tick "Nhờ phòng khác xử lý" (bao-CR-488).
    handler_dept_assigned: fromPr.handler_dept_id > 0,
    requester: fromPr.requester,
    requester_id: fromPr.requester_id,
    requester_position: fromPr.requester_position,
    //  Giữ ĐÚNG phòng + TBP của YCMH như v1 (rà mã duoc-CR-741). Gói cũ không có id thì để 0:
    //  màn không bù phòng theo hồ sơ người yêu cầu khi gói có tên phòng, backend tự tra id theo
    //  tên lúc Lưu (CR-086). Id của NGƯỜI LẬP không bao giờ dính sang.
    department_id: fromPr.department_id,
    department: fromPr.department,
    head_of_dept_id: fromPr.head_of_dept_id,
    head_of_dept: fromPr.head_of_dept,
    purpose: fromPr.purpose,
    note: [fromPr.note, `(Tạo từ YCMH ${fromPr.pr_code})`].filter(Boolean).join('\n'),
    lines,
  }
}

/**
 * Phiếu điền sẵn từ YCMH có giữ phòng nguồn không — có thì màn tạo YCBG KHÔNG được bù phòng
 * theo hồ sơ hiện tại của người yêu cầu (nhịp CR-086), kẻo ghi đè phòng của YCMH (rà mã
 * duoc-CR-741, khớp v1: v1 chép nguyên tên phòng của YCMH).
 */
export function keepsSourceDepartment(fromPr: SurveyRequestFromPurchaseRequestState | null): boolean {
  return !!fromPr?.department.trim()
}
