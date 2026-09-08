import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type {
  PurchaseOrderDelivery,
  PurchaseOrderDetail,
  PurchaseOrderItem,
} from '../types/purchase-order-detail'

const BASE_URL = '/api/purchase-orders'

/** Dòng hàng gửi lên khi tạo/sửa — chỉ các cột người dùng nhập. */
export interface PurchaseOrderItemPayload
  extends Pick<
    PurchaseOrderItem,
    | 'product_code'
    | 'product_name'
    | 'invoice_name'
    | 'item_group'
    | 'spec'
    | 'fg_code'
    | 'fg_name'
    | 'invoice_no'
    | 'invoice_date'
    | 'document_delivery_date'
    | 'supplier_ready'
    | 'required_date'
    | 'expected_date'
    | 'unit'
    | 'qty_request'
    | 'qty_order'
    | 'price'
    | 'vat'
    | 'warehouse_code'
    | 'note'
  > {
  id?: number
  deliveries: PurchaseOrderDelivery[]
}

export interface PurchaseOrderPayload {
  misa_code: string
  pr_code: string
  survey_code: string
  company_id: number
  supplier_code: string
  supplier_name: string
  department: string
  nspt: string
  order_date: string
  vat_rate: number
  payment_terms: string
  is_urgent: boolean
  note: string
  items: PurchaseOrderItemPayload[]
}

/**
 * Tầng API của Đơn mua hàng.
 *
 * Luồng trạng thái: `draft` → submit → `submitted` → approve → `approved`
 * → (nhận hàng) `partial`/`received` → complete → `completed` (reopen mở lại).
 * Nhánh phụ: return (`rejected`, sửa & gửi lại được), reject/cancel
 * (`cancelled`, khóa đơn).
 */
/**
 * Dữ liệu cho bản in: đơn + hồ sơ công ty / NCC / kho mà bản in cần nhưng bản
 * chi tiết không trả (địa chỉ, MST, mail nhận hóa đơn…).
 */
export interface PurchaseOrderPrintData extends PurchaseOrderDetail {
  company: {
    name?: string
    address?: string
    tax_code?: string
    invoice_email?: string
  }
  supplier: {
    name?: string
    address?: string
    tax_code?: string
    payment_terms?: string
  }
  warehouse: { code?: string; name?: string; address?: string }
  /** Mã kho -> tên kho, cho cột "Tên kho nhập". */
  wh_names: Record<string, string>
  /**
   * Họ tên + ảnh chữ ký cho các ô ký. Đơn chưa duyệt thì `approver_*` rỗng,
   * còn ô "Người nhận" không có ở đây vì luôn ký tươi lúc giao nhận.
   */
  signers?: PurchaseOrderSigners
}

export interface PurchaseOrderSigners {
  creator_name: string
  creator_signature: string
  approver_name: string
  approver_signature: string
}

export const purchaseOrderApi = {
  getById: (id: number) => apiGet<PurchaseOrderDetail>(`${BASE_URL}/${id}`),

  getPrintData: (id: number) => apiGet<PurchaseOrderPrintData>(`${BASE_URL}/${id}/print`),

  create: (payload: PurchaseOrderPayload) =>
    apiPost<PurchaseOrderDetail>(BASE_URL, payload),

  update: (id: number, payload: PurchaseOrderPayload) =>
    apiPatch<PurchaseOrderDetail>(`${BASE_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  /** Nhân bản thành đơn Nháp mới. */
  copy: (id: number) => apiPost<PurchaseOrderDetail>(`${BASE_URL}/${id}/copy`, {}),

  submit: (id: number) => apiPost<PurchaseOrderDetail>(`${BASE_URL}/${id}/submit`, {}),
  approve: (id: number) => apiPost<PurchaseOrderDetail>(`${BASE_URL}/${id}/approve`, {}),
  complete: (id: number) => apiPost<PurchaseOrderDetail>(`${BASE_URL}/${id}/complete`, {}),
  /** Mở lại đơn đã hoàn thành để xử lý tiếp (nhập số HĐ, tạo YCTT…). */
  reopen: (id: number) => apiPost<PurchaseOrderDetail>(`${BASE_URL}/${id}/reopen`, {}),

  /** Bốn thao tác dưới đều cần lý do — lý do vào nhật ký thao tác. */
  reject: (id: number, reason: string) =>
    apiPost<PurchaseOrderDetail>(`${BASE_URL}/${id}/reject`, { reason }),
  /** Hủy duyệt: đưa đơn ĐÃ DUYỆT về Nháp để sửa rồi gửi duyệt lại (CR-108). */
  unapprove: (id: number, reason: string) =>
    apiPost<PurchaseOrderDetail>(`${BASE_URL}/${id}/unapprove`, { reason }),
  returnToCreator: (id: number, reason: string) =>
    apiPost<PurchaseOrderDetail>(`${BASE_URL}/${id}/return`, { reason }),
  cancel: (id: number, reason: string) =>
    apiPost<PurchaseOrderDetail>(`${BASE_URL}/${id}/cancel`, { reason }),

  /** Tình trạng hồ sơ chứng từ — cập nhật được cả khi đơn đã hoàn thành. */
  setDocumentStatus: (id: number, documentStatus: string) =>
    apiPatch<PurchaseOrderDetail>(`${BASE_URL}/${id}/document-status`, {
      document_status: documentStatus,
    }),

  /**
   * Đổi tiến độ MỘT dòng. `status = '__resume__'` để tiếp tục sau khi Tạm ngưng;
   * Tạm ngưng / Hủy đơn bắt buộc có `reason`.
   */
  setItemProgress: (id: number, itemId: number, status: string, reason = '') =>
    apiPost<PurchaseOrderDetail>(`${BASE_URL}/${id}/items/${itemId}/progress`, {
      status,
      reason,
    }),
}
