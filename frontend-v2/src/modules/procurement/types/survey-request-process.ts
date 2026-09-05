/**
 * Hình dạng dữ liệu khung XỬ LÝ KHẢO SÁT (`GET /api/survey-requests/{id}/process`) —
 * bản NỘI BỘ dành cho NSTM / Admin thu mua, CÓ đủ danh tính NCC (`supplier_*`,
 * `snap_internal_code`).
 *
 * CỐ Ý tách khỏi `survey-request-detail.ts`: bên đó là bản đã LỌC cho người yêu
 * cầu (whitelist `_OPT_PUBLIC_FIELDS` ở backend, NCC chỉ còn số ẩn danh). Gộp hai
 * hình dạng vào một kiểu là mở đường cho code hiện nhầm tên NCC với người YC.
 */

/** Phương án trên một dòng — bản ĐẦY ĐỦ, kèm NCC. */
export interface SurveyProcessOption {
  id: number
  public_id: number
  display_label: string
  is_chosen: boolean
  system_product_code: string
  /** Nguồn của phương án (`tab_survey_product_line`) — để lọc dòng khảo sát ĐÃ GẮN khỏi bảng chọn. */
  product_survey_line_id: number
  snap_product_name: string
  snap_spec: string
  snap_origin: string
  snap_quote_unit: string
  snap_moq: number
  snap_price_by_volume: number
  snap_volume_range: string
  snap_vat: number
  snap_delivery_time: string
  snap_delivery_place: string
  snap_shipping_cost: number
  snap_sample_ready: boolean
  snap_lab_result: string
  snap_internal_code: string
  supplier_code: string
  supplier_name: string
  nstm_note: string
}

/** Một dòng cần khảo sát trong khung xử lý. */
export interface SurveyProcessLine {
  id: number
  internal_line_code: string
  item_group: string
  requirement_detail: string
  other_requirement: string
  request_qty: number
  uom: string
  proposed_price: number
  assignee: string
  assignee_name: string
  is_completed: boolean
  no_option: boolean
  /** Mã trạng thái dòng — `confirmed` là người yêu cầu đã chốt phương án (P6-3). */
  line_status: string
  options: SurveyProcessOption[]
  /**
   * Người đang xem có được GẮN/XÓA phương án trên dòng này không. Admin TM thấy
   * mọi dòng nhưng chỉ sửa được dòng mình phụ trách — dòng khác hiện read-only.
   */
  can_process: boolean
}

/** Đầu phiếu + các dòng NGƯỜI XEM được thấy (NSTM chỉ thấy dòng mình phụ trách). */
export interface SurveyRequestProcess {
  id: number
  code: string
  status: string
  request_date: string
  department: string
  requester: string
  company_id: number
  lines: SurveyProcessLine[]
}

/** Một dòng KẾT QUẢ KHẢO SÁT ĐÃ DUYỆT chọn được để gắn làm phương án. */
export interface AvailableSurveyLine {
  id: number
  supplier_code: string
  supplier_name: string
  /** Mã SP theo NCC. */
  internal_code: string
  product_name: string
  spec: string
  origin: string
  quote_unit: string
  moq: number
  price_by_volume: number
  volume_range: string
  vat: number
  delivery_time: string
  delivery_place: string
  shipping_cost: number
  sample_ready: boolean
  lab_result: string
  /** Phân loại của Phiếu khảo sát cha — để cảnh báo khi KHÁC phân loại dòng. */
  survey_item_group: string
  survey_code: string
  /** Mã VTBB/VL, lấy từ header phiếu khảo sát. */
  survey_item_code: string
  /** Ngày trả kết quả của dòng NCC — hiển thị làm "Ngày khảo sát". */
  result_date: string
}

export interface AvailableSurveyLinesResult {
  items: AvailableSurveyLine[]
  total: number
}

/** Tham số lọc bảng "Kết quả khảo sát đã duyệt" — backend đòi ÍT NHẤT một tiêu chí. */
export interface AvailableSurveyLinesParams {
  supplier_code: string
  item_group: string
  search: string
  /** Trang 1-based (khớp backend). */
  page: number
  page_size: number
}

/** Trạng thái phiếu cho phép gắn/xóa phương án (backend chặn ngoài hai mốc này). */
export const PROCESSABLE_STATUSES = ['processing', 'survey_done'] as const

export function isSurveyRequestProcessable(status: string): boolean {
  return (PROCESSABLE_STATUSES as readonly string[]).includes(status)
}
