/**
 * Phiếu YÊU CẦU BÁO GIÁ (YCBG) — bản chi tiết.
 *
 * Một phiếu đi qua HAI khung nhìn khác nhau, backend trả hai hình dạng khác nhau:
 * - `GET /api/survey-requests/{id}` — khung của NGƯỜI YÊU CẦU: đầu phiếu + dòng yêu cầu.
 * - `GET /api/survey-requests/{id}/result` — khung KẾT QUẢ: thêm phương án khảo sát,
 *   **đã bỏ tên/mã nhà cung cấp ngay ở backend** (whitelist `_OPT_PUBLIC_FIELDS`), NCC
 *   chỉ còn số thứ tự ẩn danh. Đừng gộp hai kiểu này làm một: gộp là sớm muộn cũng có
 *   người đọc `supplier_code` ở khung kết quả rồi tưởng backend quên trả.
 */

/**
 * Nhãn trạng thái phiếu dùng chung với màn danh sách — `SR_STATUS_LABELS` trong
 * `./purchase-document`. Đừng chép lại bảng nhãn ở đây: chép là hai màn lệch chữ.
 * (`cancelled` = từ chối hẳn, khác `rejected` = trả lại để sửa.)
 */

/** Trạng thái DÒNG do người yêu cầu chốt (khác `progress_state` — cái đó backend suy ra). */
export const LINE_STATUS_RESURVEY = 'resurvey'
export const LINE_STATUS_COMPLETED = 'completed'

/** Một dòng sản phẩm cần khảo sát — `lines[]` của `GET /api/survey-requests/{id}`. */
export interface SurveyRequestLine {
  /** Thiếu / 0 = dòng mới chưa lưu. */
  id?: number
  /** Mã dòng nội bộ, KHÔNG hiện cho người yêu cầu. */
  internal_line_code?: string
  item_group: string
  requirement_detail: string
  other_requirement: string
  request_qty: number
  uom: string
  /** Giá đề xuất, giữ tới 4 số lẻ như mọi đơn giá trong hệ. */
  proposed_price: number

  /** Mốc của thu mua — chỉ người xử lý được xem. */
  received_date: string
  result_due_date: string
  result_date: string
  /** MÃ nhân sự thu mua phụ trách dòng (không phải id). */
  assignee: string
  assignee_name: string

  pr_id: number
  pr_code: string
  is_completed: boolean
  line_status: string
  /** Đã khảo sát nhưng không có phương án nào phù hợp. */
  no_option: boolean

  /** Backend đếm sẵn, đừng tự đếm lại từ `options` (khung này không trả options). */
  option_count: number
  has_chosen: boolean
  /**
   * CR-077: nhãn tiến độ dòng do BACKEND suy, dùng chung với màn Tiến độ báo giá.
   * FE tự tính lại là hai màn hiện hai chữ khác nhau cho cùng một dòng.
   */
  progress_state: string
  progress_tone: string
}

/** Đầu phiếu + dòng — `GET /api/survey-requests/{id}`. */
export interface SurveyRequestDetail {
  id: number
  code: string
  company_id: number
  requester: string
  requester_id: number
  requester_position: string
  /** CR-086/087: id là nguồn sự thật, hai cột tên bên dưới là bản chụp để in. */
  department_id: number
  department: string
  head_of_dept_id: number
  head_of_dept: string
  purpose: string
  request_date: string
  status: string
  note: string
  reject_reason: string

  created_at: string
  created_by: number

  lines: SurveyRequestLine[]
}

/** Đính kèm của một phương án — lấy từ dòng khảo sát nguồn. */
export interface SurveyOptionAttachment {
  file_id: number
  filename: string
  url: string
  content_type: string
  size: number
}

/** YCMH đã sinh ra từ một phương án. */
export interface SurveyOptionPr {
  id: number
  code: string
  date: string
  status: string
}

/**
 * Một PHƯƠNG ÁN khảo sát ở khung kết quả — **không có trường nào lộ NCC**.
 * `ncc_ref` là số ẩn danh: cùng số = cùng nhà cung cấp, để so được giữa các sản phẩm.
 */
export interface SurveyResultOption {
  id: number
  public_id: number
  display_label: string
  is_chosen: boolean
  ncc_ref: number
  /** Mã vật tư của chính người yêu cầu — không phải mã của NCC. */
  system_product_code: string
  snap_product_name: string
  snap_spec: string
  snap_origin: string
  snap_quote_unit: string
  snap_moq: string
  snap_price_by_volume: string
  snap_volume_range: string
  snap_vat: string
  snap_delivery_time: string
  snap_delivery_place: string
  snap_shipping_cost: string
  snap_sample_ready: string
  snap_lab_result: string
  /** Ngày dòng khảo sát nguồn trả kết quả (không lộ khảo sát nào). */
  survey_result_date: string
  /** CR-147 main (ticket #11): 'Ghi chú' của khảo sát SP — đọc live, NSTM sửa là thấy theo. */
  survey_note: string
  /** CR-147 main: 'Lý do NSPT' — bản chụp lúc tạo phương án. Khách chấp nhận rủi ro lộ tên NCC trong chữ tự do. */
  nstm_note: string
  attachments: SurveyOptionAttachment[]
  ycmh_list: SurveyOptionPr[]
  ycmh_count: number
}

/** Dòng ở khung kết quả — ít trường hơn khung đầu phiếu, kèm danh sách phương án. */
export interface SurveyResultLine {
  id: number
  item_group: string
  requirement_detail: string
  other_requirement: string
  request_qty: number
  uom: string
  proposed_price: number
  is_completed: boolean
  line_status: string
  pr_id: number
  pr_code: string
  no_option: boolean
  options: SurveyResultOption[]
  option_count: number
  has_chosen: boolean
  progress_state: string
  progress_tone: string
}

/** `GET /api/survey-requests/{id}/result`. */
export interface SurveyRequestResult {
  id: number
  code: string
  status: string
  lines: SurveyResultLine[]
}

/** Phiếu đã chốt -> khóa mọi thao tác ghi. */
export function isSurveyRequestLocked(status: string): boolean {
  return status === 'cancelled' || status === 'done'
}

/** Chỉ nháp và bị trả lại mới sửa được nội dung phiếu. */
export function isSurveyRequestEditable(status: string): boolean {
  return status === 'draft' || status === 'rejected'
}

/** Từ trạng thái này trở đi mới có kết quả khảo sát để xem. */
export function hasSurveyResult(status: string): boolean {
  return ['processing', 'survey_done', 'pr_created', 'done'].includes(status)
}
