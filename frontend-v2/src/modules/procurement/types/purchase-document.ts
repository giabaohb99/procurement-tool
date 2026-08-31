/**
 * Kiểu dữ liệu cho 4 chứng từ của luồng mua hàng, khớp đúng những cột backend
 * TRẢ VỀ Ở DANH SÁCH (không phải toàn bộ cột của bảng):
 *
 *   Yêu cầu báo giá (YCBG)  -> `/api/survey-requests`
 *   Khảo sát                -> `/api/surveys`
 *   Yêu cầu mua hàng (PYC)  -> `/api/purchase-requests`
 *   Đơn mua hàng (ĐMH)      -> `/api/purchase-orders`
 *
 * Trạng thái lưu bằng MÃ tiếng Anh (`draft`, `submitted`…), khác với các bảng
 * danh mục vốn lưu thẳng chuỗi tiếng Việt — nhãn hiển thị tra ở các map dưới.
 */

/** Yêu cầu mua hàng — `/api/purchase-requests`. */
export interface PurchaseRequest {
  id: number
  code: string
  company_id: number
  requester: string
  department: string
  purpose: string
  request_date: string
  need_date: string
  status: string
  is_urgent: boolean
  note: string
  /** Thời điểm tạo (có giờ), khác `request_date` do người dùng tự nhập. */
  created_at: string
  /** Tổng tiền gồm VAT, backend cộng từ các dòng. */
  total: number
  /** Có ít nhất một dòng "Hủy đơn" — bản cũ tô đỏ cả dòng. */
  has_cancelled_line: boolean
}

/** Yêu cầu báo giá — `/api/survey-requests`. */
export interface SurveyRequest {
  id: number
  code: string
  company_id: number
  requester: string
  department: string
  purpose: string
  request_date: string
  status: string
  note: string
  created_at: string
}

/** Đơn mua hàng — `/api/purchase-orders`. */
export interface PurchaseOrder {
  id: number
  code: string
  misa_code: string
  pr_code: string
  /** 0 = không truy được PYC gốc (dữ liệu cũ). */
  pr_id: number
  survey_code: string
  company_id: number
  supplier_code: string
  supplier_name: string
  department: string
  /** Nhân sự phụ trách. */
  nspt: string
  order_date: string
  is_urgent: boolean
  status: string
  /** Tình trạng hồ sơ chứng từ — lưu CHUỖI TIẾNG VIỆT, không phải mã. */
  document_status: string
  note: string
  created_at: string
  /** Tiền hàng. */
  amount: number
}

/** Phiếu khảo sát — `/api/surveys`. */
export interface Survey {
  id: number
  code: string
  /** `supplier` = khảo sát NCC, `product` = khảo sát sản phẩm. */
  survey_type: string
  sr_code: string
  pr_code: string
  item_group: string
  main_content: string
  item_code: string
  item_name: string
  nspt: string
  status: string
  created_at: string
}

/** Nhãn tiếng Việt của mã trạng thái, theo từng loại chứng từ. */
export const PR_STATUS_LABELS: Record<string, string> = {
  draft: 'Nháp',
  submitted: 'Chờ duyệt',
  approved: 'Đã duyệt',
  dispatched: 'Đã điều phối',
  rejected: 'Bị trả lại',
  cancelled: 'Đã từ chối',
  processing: 'Đang xử lý',
  completed: 'Hoàn thành',
}

export const SR_STATUS_LABELS: Record<string, string> = {
  draft: 'Nháp',
  submitted: 'Chờ duyệt',
  approved: 'Đã duyệt',
  processing: 'Đang xử lý',
  survey_done: 'Đã khảo sát',
  pr_created: 'Đã tạo YCMH',
  done: 'Hoàn thành',
  rejected: 'Bị trả lại',
  cancelled: 'Đã từ chối',
}

export const PO_STATUS_LABELS: Record<string, string> = {
  draft: 'Nháp',
  submitted: 'Chờ duyệt',
  approved: 'Đã duyệt',
  partial: 'Đã nhận một phần',
  received: 'Đã nhận đủ',
  completed: 'Hoàn thành',
  rejected: 'Bị trả lại',
  cancelled: 'Đã từ chối',
}

export const SURVEY_STATUS_LABELS: Record<string, string> = {
  draft: 'Nháp',
  submitted: 'Chờ duyệt',
  approved: 'Đã duyệt',
  rejected: 'Bị trả lại',
  cancelled: 'Đã từ chối',
}

/**
 * Nhãn LOẠI phiếu khảo sát.
 *
 * `combined` là loại DUY NHẤT còn sinh ra: backend đặt cứng `survey_type="combined"`
 * cho mọi phiếu tạo mới (`app/modules/survey/service.py`) vì một phiếu nay ôm cả hai
 * bảng NCC và SP. Hai mã còn lại là dữ liệu CŨ (8 phiếu `supplier`, 9 phiếu `product`
 * trên bản dev) — vẫn phải khai ở đây, bỏ đi là 17 phiếu đó hiện mã tiếng Anh trần.
 *
 * Thiếu `combined` chính là lỗi đã lủng: cột "Loại" in thẳng chữ `combined` ra màn
 * hình, và ô lọc không có mục nào chọn được đúng 2.693 phiếu đang có.
 */
export const SURVEY_TYPE_LABELS: Record<string, string> = {
  combined: 'Khảo sát NCC & SP',
  supplier: 'Khảo sát NCC',
  product: 'Khảo sát SP',
}

/** Options cho ô select trên thanh công cụ / bộ lọc nâng cao. */
export function statusOptions(labels: Record<string, string>) {
  return Object.entries(labels).map(([value, label]) => ({ value, label }))
}
