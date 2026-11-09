import type { AssistantDraft } from '../utils/assistant-draft'
import type { PurchaseRequestDetail } from '../types/purchase-request-detail'

/** Một dòng YCBG điền sẵn từ dòng YCMH — đúng khuôn `createSurveyRequest` của bản v1. */
export interface SurveyRequestLineFromPurchaseRequest {
  received_date: string
  result_due_date: string
  item_group: string
  requirement_detail: string
  other_requirement: string
  request_qty: number
  uom: string
  proposed_price: number
  /** CR-027: id dòng YCMH nguồn — ảnh đối chiếu của dòng đó được kéo sang khi Lưu YCBG. */
  src_pr_item_id: number
}

/** Gói `state.fromPr` mà màn tạo YCBG bản v1 đọc (`SurveyRequestDetail.tsx`). */
export interface SurveyRequestFromPurchaseRequest {
  pr_id: number
  pr_code: string
  company_id: number
  requester: string
  requester_id: number
  requester_position: string
  department: string
  /**
   * Rà mã duoc-CR-741: id phòng / TBP của YCMH nguồn. Bản v1 chỉ chép TÊN; v2 chép thêm id để
   * màn YCBG KHÔNG bù phòng theo hồ sơ hiện tại của người yêu cầu (CR-086) mà giữ đúng phòng
   * của YCMH — khác nhau khi YCMH lập cho phòng khác hoặc người yêu cầu đã chuyển phòng.
   * Tùy chọn vì gói cũ còn nằm trong lịch sử trình duyệt có thể thiếu.
   */
  department_id?: number
  head_of_dept: string
  head_of_dept_id?: number
  purpose: string
  note: string
  lines: SurveyRequestLineFromPurchaseRequest[]
}

/**
 * Nút *Tạo yêu cầu báo giá* của YCMH bị trả lại / đã từ chối (CR-026, dời từ v1 ở duoc-CR-741):
 * dựng dữ liệu điền sẵn cho màn tạo YCBG. KHÔNG ghi gì xuống DB — người dùng rà lại rồi tự
 * bấm Lưu bên màn YCBG.
 *
 * Trả HAI gói vì màn tạo YCBG của v2 hiện mới đọc `assistantDraft` (khuôn bản nháp Trợ lý AI):
 *
 * - `fromPr` — đủ như v1 (người yêu cầu, phòng ban, TBP, id dòng nguồn để kéo ảnh). Màn YCBG
 *   v2 chưa đọc gói này; khi màn đó đọc thì ưu tiên nó.
 * - `assistantDraft` — phần màn YCBG v2 đã điền được hôm nay: mục đích, ghi chú, công ty, dòng.
 *
 * YCBG không có ô mã / tên hàng nên tên hàng gộp vào *Chi tiết thông số*, kẻo mất thông tin.
 */
export function buildSurveyRequestPrefill(purchaseRequest: PurchaseRequestDetail): {
  fromPr: SurveyRequestFromPurchaseRequest
  assistantDraft: AssistantDraft
} {
  const lines = purchaseRequest.items
    .filter((item) => item.product_name.trim())
    .map<SurveyRequestLineFromPurchaseRequest>((item) => ({
      received_date: '',
      result_due_date: '',
      item_group: item.item_group || '',
      requirement_detail: [item.product_name, item.group_desc].filter(Boolean).join(' — '),
      other_requirement: item.note || '',
      request_qty: Number(item.qty) || 0,
      uom: item.unit || '',
      proposed_price: Number(item.price) || 0,
      src_pr_item_id: item.id || 0,
    }))

  const fromPr: SurveyRequestFromPurchaseRequest = {
    pr_id: purchaseRequest.id || 0,
    pr_code: purchaseRequest.code,
    company_id: purchaseRequest.company_id || 0,
    requester: purchaseRequest.requester || '',
    requester_id: purchaseRequest.requester_id || 0,
    requester_position: purchaseRequest.requester_position || '',
    department: purchaseRequest.department || '',
    department_id: purchaseRequest.department_id || 0,
    head_of_dept: purchaseRequest.head_of_dept || '',
    head_of_dept_id: purchaseRequest.head_of_dept_id || 0,
    purpose: purchaseRequest.purpose || '',
    note: purchaseRequest.note || '',
    lines,
  }

  const assistantDraft: AssistantDraft = {
    purpose: fromPr.purpose,
    //  Bản v1 ghi nguồn vào ghi chú của YCBG mới: "(Tạo từ YCMH <mã>)".
    note: [fromPr.note, `(Tạo từ YCMH ${fromPr.pr_code})`].filter(Boolean).join('\n'),
    company_id: fromPr.company_id,
    company_name: purchaseRequest.company_name || '',
    lines: lines.map((line) => ({
      requirement_detail: line.requirement_detail,
      item_group: line.item_group,
      request_qty: line.request_qty,
      uom: line.uom,
      proposed_price: line.proposed_price,
      other_requirement: line.other_requirement,
      result_due_date: line.result_due_date,
    })),
  }

  return { fromPr, assistantDraft }
}
