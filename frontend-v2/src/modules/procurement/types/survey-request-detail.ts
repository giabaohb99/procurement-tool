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
/**
 * P6-3 (bao-CR-281): "đã chốt phương án" — khóa lựa chọn để thu mua tạo THẲNG
 * đơn mua hàng. Chỉ set qua endpoint `confirm-option` riêng (cần dòng đang chọn
 * phương án), KHÔNG đi qua dropdown `line-status` như hai giá trị trên.
 */
export const LINE_STATUS_CONFIRMED = 'confirmed'

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
  /**
   * Mã hàng hệ thống của dòng (P6-1/P6-2, bao-CR-277/280). Rỗng = chưa có mã —
   * người YC chọn phương án mang mã thì backend tự điền mã đó lên dòng.
   * bao-CR-289: người YC cũng CHỌN được mã ngay lúc lập phiếu (không bắt buộc).
   */
  product_code: string
  /**
   * P6-1 (bao-CR-277) + bao-CR-289: bộ trường YCMH mang lên dòng phiếu gộp —
   * kho nhận / ngày cần hàng / VAT% đi qua payload lưu phiếu như trường thường.
   */
  warehouse: string
  required_date: string
  vat_pct: number
  /** P6-4: hai cột tiến độ nhận/đặt do đồng bộ từ ĐMH ghi — client CHỈ ĐỌC. */
  qty_ordered: number
  qty_received: number
  /**
   * bao-CR-289: NSTM cập nhật qua endpoint `lines/{id}/progress` RIÊNG — cố ý
   * không nằm trong payload lưu phiếu để người YC sửa phiếu không xóa mất.
   */
  expected_date: string
  progress_note: string
  /**
   * bao-CR-291: ghi chú RIÊNG của thu mua (mirror `note` của dòng YCMH). Đi cùng
   * đường ghi với hai trường trên — người YC không đè được.
   */
  purchaser_note: string

  /**
   * bao-CR-291: tên + ảnh gốc tra LIVE từ danh mục theo `product_code`, backend chỉ
   * TRẢ chứ không nhận (dòng không lưu tên hàng). Dòng chưa có mã thì rỗng/0 và giao
   * diện nhắc người lập mô tả vào ô Chi tiết thông số.
   */
  product_id?: number
  product_name?: string
  product_thumbnail_url?: string

  /** Mốc của thu mua — chỉ người xử lý được xem. */
  received_date: string
  result_due_date: string
  result_date: string
  /** MÃ nhân sự thu mua phụ trách dòng (không phải id). */
  assignee: string
  assignee_name: string

  pr_id: number
  pr_code: string
  /** P6-3 (bao-CR-281): ĐMH gần nhất tạo THẲNG từ dòng (luồng v2 bỏ bước YCMH). */
  po_id: number
  po_code: string
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
  /** bao-CR-289: cờ Đơn gấp (mirror YCMH). */
  is_urgent: boolean
  reject_reason: string

  /**
   * P6-9 (bao-CR-287): NCC do NGƯỜI YÊU CẦU đề xuất — mirror cụm `req` của YCMH,
   * cũng ở đầu phiếu (một NCC cho cả phiếu). Dùng cho BẢN IN luồng gộp: dòng CHƯA
   * chốt phương án in cụm này ở cột NCC thay cho NCC khảo sát (vốn phải giấu).
   */
  suggested_supplier: string
  suggested_supplier_tax_code: string
  suggested_supplier_contact: string

  created_at: string
  created_by: number

  /**
   * P6-8 (bao-CR-286): cờ luồng gộp chứng từ (chốt phương án → tạo thẳng ĐMH),
   * backend đọc từ Cấu hình hệ thống. TẮT thì ẩn nút Chốt/Tạo ĐMH — backend vẫn chặn 400.
   */
  merged_flow_enabled: boolean

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
  /**
   * P6-2 (bao-CR-280): dòng ĐÃ CÓ mã thì backend chỉ trả phương án khớp mã này
   * (kèm phương án chưa gắn mã / đang chọn); dòng CHƯA có mã thì chọn phương án
   * mang mã sẽ tự điền mã lên dòng, bỏ chọn thì gỡ lại.
   */
  product_code: string
  is_completed: boolean
  line_status: string
  pr_id: number
  pr_code: string
  /** P6-3 (bao-CR-281): ĐMH gần nhất tạo THẲNG từ dòng (luồng v2 bỏ bước YCMH). */
  po_id: number
  po_code: string
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
  /** P6-8 (bao-CR-286): TẮT thì ẩn nút Chốt phương án (Bỏ chốt vẫn hiện để gỡ dòng kẹt khóa). */
  merged_flow_enabled: boolean
  lines: SurveyResultLine[]
}

// ───────────── P6-9 (bao-CR-287): hai bản in của luồng gộp ─────────────

/**
 * Dòng ở BẢN IN NGƯỜI YÊU CẦU (`GET /{id}/print`). Backend chỉ lộ NCC của phương
 * án khi dòng ĐÃ CHỐT (`line_status === confirmed`); dòng chưa chốt
 * `print_supplier_name` là NCC người yêu cầu tự nhập ở đầu phiếu.
 */
export interface SurveyRequestPrintLine extends SurveyRequestLine {
  print_supplier_name: string
  print_supplier_source: 'confirmed' | 'requester'
  /** 0 / rỗng khi dòng chưa chốt — khi đó in giá đề xuất của người yêu cầu. */
  chosen_price: number
  chosen_vat: number
  chosen_delivery_time: string
  // bao-CR-288 từng khai lại warehouse/required_date/vat_pct ở đây; bao-CR-289 đưa
  // ba trường đó lên thẳng SurveyRequestLine nên bản in kế thừa sẵn, khỏi khai lại.
}

export interface SurveyRequestPrint extends Omit<SurveyRequestDetail, 'lines'> {
  lines: SurveyRequestPrintLine[]
}

/** Dòng đã chốt trong MỘT nhóm NCC của bản in thu mua (`GET /{id}/print-purchasing`). */
export interface SurveyRequestPurchasingLine {
  id: number
  item_group: string
  requirement_detail: string
  other_requirement: string
  request_qty: number
  uom: string
  product_code: string
  chosen_price: number
  chosen_vat: number
  chosen_delivery_time: string
  chosen_product_name: string
  chosen_quote_unit: string
}

/** Một NHÓM = một NCC — mỗi nhóm in thành một phiếu riêng. */
export interface SurveyRequestPurchasingGroup {
  supplier_code: string
  supplier_name: string
  lines: SurveyRequestPurchasingLine[]
}

/** ĐMH đã sinh từ phiếu (bảng SurveyRequestPo), in kèm cuối bộ bản in thu mua. */
export interface SurveyRequestPurchasingPo {
  id: number
  code: string
  supplier_code: string
  supplier_name: string
  status: string
}

/**
 * `GET /{id}/print-purchasing` — bản in THU MUA tách theo NCC, backend gác
 * `supplier.read` (người yêu cầu gọi là 403).
 */
export interface SurveyRequestPurchasingPrint {
  id: number
  code: string
  status: string
  company_id: number
  requester: string
  requester_position: string
  department: string
  purpose: string
  request_date: string
  note: string
  groups: SurveyRequestPurchasingGroup[]
  purchase_orders: SurveyRequestPurchasingPo[]
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
