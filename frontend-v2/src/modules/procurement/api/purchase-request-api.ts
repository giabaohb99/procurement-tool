import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type {
  DeptHeadCandidate,
  PurchaseRequestDetail,
  PurchaseRequestItem,
} from '../types/purchase-request-detail'

const BASE_URL = '/api/purchase-requests'

/** Phần header + dòng hàng gửi lên khi tạo/sửa phiếu. */
export interface PurchaseRequestPayload {
  company_id: number
  requester: string
  requester_id: number
  requester_position: string
  department: string
  head_of_dept: string
  /** CR-071 — id nhân sự TBP đứng tên trên phiếu (0 = theo mặc định phòng). */
  head_of_dept_id: number
  purpose: string
  request_date: string
  need_date: string
  is_urgent: boolean
  vat_rate: number
  note: string
  show_code_on_print: boolean
  quote_filename?: string
  quote_file_url?: string
  supplier_req: { name: string; tax_code: string; contact: string }
  supplier_pur?: { name: string; tax_code: string; contact: string }
  items: Partial<PurchaseRequestItem>[]
}

/**
 * Tầng API của phiếu Yêu cầu mua hàng.
 *
 * Luồng trạng thái: `draft` → submit → `submitted` → approve → `approved`
 * → dispatch → `dispatched` → complete → `completed`.
 * Nhánh phụ: reject (trả về `rejected` để sửa lại), cancel (`cancelled`),
 * return (trả phiếu đã duyệt về cho người yêu cầu sửa).
 */
export const purchaseRequestApi = {
  getById: (id: number) => apiGet<PurchaseRequestDetail>(`${BASE_URL}/${id}`),

  create: (payload: PurchaseRequestPayload) =>
    apiPost<PurchaseRequestDetail>(BASE_URL, payload),

  update: (id: number, payload: PurchaseRequestPayload) =>
    apiPatch<PurchaseRequestDetail>(`${BASE_URL}/${id}`, payload),

  /** Xóa hẳn phiếu. Endpoint nhận danh sách id qua query, không phải path. */
  remove: (id: number) => apiDelete<null>(`${BASE_URL}?ids=${id}`),

  /** Nhân bản thành phiếu nháp mới. */
  copy: (id: number) => apiPost<PurchaseRequestDetail>(`${BASE_URL}/${id}/copy`, {}),

  submit: (id: number) => apiPost<PurchaseRequestDetail>(`${BASE_URL}/${id}/submit`, {}),
  approve: (id: number) => apiPost<PurchaseRequestDetail>(`${BASE_URL}/${id}/approve`, {}),
  dispatch: (id: number) => apiPost<PurchaseRequestDetail>(`${BASE_URL}/${id}/dispatch`, {}),
  complete: (id: number) => apiPost<PurchaseRequestDetail>(`${BASE_URL}/${id}/complete`, {}),

  /** Ba thao tác dưới đây đều BẮT BUỘC nêu lý do — lý do vào nhật ký thao tác. */
  reject: (id: number, reason: string) =>
    apiPost<PurchaseRequestDetail>(`${BASE_URL}/${id}/reject`, { reason }),
  cancel: (id: number, reason: string) =>
    apiPost<PurchaseRequestDetail>(`${BASE_URL}/${id}/cancel`, { reason }),
  /** Trả phiếu ĐÃ DUYỆT về cho người yêu cầu sửa lại. */
  returnToRequester: (id: number, reason: string) =>
    apiPost<PurchaseRequestDetail>(`${BASE_URL}/${id}/return`, { reason }),

  /** Gán nhân sự thu mua phụ trách cho từng dòng. */
  assign: (id: number, items: { id: number; assignee: string }[]) =>
    apiPatch<PurchaseRequestDetail>(`${BASE_URL}/${id}/assign`, { items }),

  /** Cập nhật tiến độ của dòng (trạng thái, ghi chú, ngày dự kiến có hàng). */
  updateItemStatus: (
    id: number,
    items: {
      id: number
      line_status: string
      progress_note?: string
      note?: string
      expected_date?: string
      /** Bắt buộc khi ĐỔI ngày dự kiến đã có trước đó. */
      expected_date_reason?: string
    }[],
  ) => apiPatch<PurchaseRequestDetail>(`${BASE_URL}/${id}/item-status`, { items }),

  setUrgent: (id: number, isUrgent: boolean) =>
    apiPatch<PurchaseRequestDetail>(`${BASE_URL}/${id}/urgent`, { is_urgent: isUrgent }),

  /** Trưởng bộ phận hiện tại của một phòng — người yêu cầu không xem được DS nhân sự. */
  getDeptHead: (department: string) =>
    apiGet<{ head_of_dept: string }>(`${BASE_URL}/meta/dept-head`, {
      params: { department },
    }),

  /**
   * CR-071 — những người duyệt được phiếu này, để ô "Trưởng bộ phận" cho chọn.
   * Backend lọc bằng chính luật phạm vi nên danh sách có thể rỗng.
   */
  getDeptHeadCandidates: (id: number) =>
    apiGet<{ items: DeptHeadCandidate[] }>(`${BASE_URL}/${id}/dept-head-candidates`),

  /** Số lượng ĐÃ ĐẶT theo mã hàng, gộp mọi ĐMH sinh từ phiếu này. */
  getOrderProgress: (id: number) =>
    apiGet<{ ordered: Record<string, number> }>(`${BASE_URL}/${id}/order-progress`),
}
