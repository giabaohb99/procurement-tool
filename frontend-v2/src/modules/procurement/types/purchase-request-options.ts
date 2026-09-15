/**
 * bao-CR-310 — PHƯƠNG ÁN (báo giá) gắn trên TỪNG DÒNG của Yêu cầu mua hàng.
 *
 * NSTM gắn tối đa 5 phương án cho mỗi dòng mình phụ trách (từ kho khảo sát đã
 * duyệt hoặc nhập tay), rồi NGƯỜI YÊU CẦU hoặc người giữ quyền duyệt YCMH chốt
 * một phương án. Backend che danh tính NCC (supplier_code/supplier_name/
 * supplier_survey_id/snap_internal_code trả chuỗi rỗng) khi người xem thiếu
 * quyền `supplier:read` — giao diện chỉ việc ẩn cột, đừng tự suy danh tính.
 */
/** Trần số phương án trên một dòng — phải khớp MAX_OPTIONS_PER_LINE của backend. */
export const MAX_OPTIONS_PER_LINE = 5

/**
 * Nguồn của phương án — khớp `PR_OPT_*` trong `constants.py` của backend.
 * ORIGINAL = "Phương án 0" (H.10 doc 03): hệ thống tự sinh từ CHÍNH DÒNG YÊU CẦU
 * khi phiếu được điều phối — chưa có NCC, sửa được, không xóa được, đứng ngoài
 * trần 5 và không tính vào `option_count`.
 */
export const PR_OPTION_SOURCE_SURVEY = 1
export const PR_OPTION_SOURCE_MANUAL = 2
export const PR_OPTION_SOURCE_ORIGINAL = 3

/**
 * Các trạng thái YCMH cho phép GẮN / SỬA / CHỐT phương án — khớp STAGE_OPEN của
 * `option_service.py`: từ lúc thu mua tiếp nhận phiếu tới trước khi phiếu đóng.
 * XEM phương án thì không bị chặn theo trạng thái (phiếu đã đóng vẫn xem được).
 */
export const PR_OPTION_STAGE_OPEN = [
  'dispatched',
  'processing',
  'purchasing',
  'purchased',
] as const

export function isPrOptionStageOpen(status: string): boolean {
  return (PR_OPTION_STAGE_OPEN as readonly string[]).includes(status)
}

/** Một phương án trên dòng YCMH — hình dạng `_out_option` của backend. */
export interface PurchaseRequestOption {
  id: number
  pr_item_id: number
  /** 1 = từ kho khảo sát, 2 = nhập tay. Nhãn hiển thị nằm ở `source_label`. */
  source: number
  source_label: string
  /** id dòng khảo sát gốc — 0/null với phương án nhập tay. */
  product_survey_line_id: number | null
  /** Số thứ tự bền trong dòng ("Phương án {public_id}"), không đánh lại khi gỡ. */
  public_id: number
  display_label: string
  is_chosen: boolean
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
  snap_shipping_cost: string
  snap_sample_ready: string
  snap_lab_result: string
  nstm_note: string
  created_at: string
  /** Bốn trường dưới bị backend TRẢ RỖNG khi người xem thiếu `supplier:read`. */
  supplier_code: string
  supplier_name: string
  supplier_survey_id: number
  snap_internal_code: string
}

/**
 * Một dòng "kết quả khảo sát đã duyệt" chọn được cho dòng YCMH — trả từ
 * `GET /{id}/items/{itemId}/available-survey-lines`. Khác AvailableSurveyLine
 * của YCBG (CR-222): không có `sample_ready`, thêm `survey_item_group` để cảnh
 * báo khi phân loại của dòng khảo sát lệch với phân loại của dòng YCMH.
 */
export interface AvailablePrSurveyLine {
  id: number
  supplier_code: string
  supplier_name: string
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
  shipping_cost: string
  lab_result: string
  result_date: string
  survey_code: string
  survey_item_code: string
  survey_item_group: string
}

export interface AvailablePrSurveyLinesResult {
  items: AvailablePrSurveyLine[]
  total: number
}

export interface AvailablePrSurveyLinesParams {
  supplier_code?: string
  item_group?: string
  search?: string
  page?: number
  page_size?: number
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
}

/** Thân `POST .../options/manual` — backend đòi có NCC (mã HOẶC tên). */
export interface PrOptionManualPayload {
  supplier_code?: string
  supplier_name?: string
  snap_product_name?: string
  snap_spec?: string
  snap_origin?: string
  snap_quote_unit?: string
  snap_moq?: number
  snap_price_by_volume?: number
  snap_volume_range?: string
  /** 0 ≤ vat < 100; bỏ trống thì backend lấy VAT của dòng YCMH. */
  snap_vat?: number | null
  snap_delivery_time?: string
  snap_delivery_place?: string
  snap_shipping_cost?: string
  snap_internal_code?: string
  nstm_note?: string
}

/**
 * Thân `PATCH .../options/{oid}/supplier` — khe H.10.4: thu mua (write +
 * supplier:read) điền/sửa NCC (kèm giá nếu cần) trên phương án 0 / nhập tay,
 * dùng được CẢ SAU khi dòng đã chốt hoàn thành. Backend đòi có mã HOẶC tên NCC
 * và từ chối phương án lấy từ khảo sát.
 */
export interface PrOptionSupplierPayload {
  supplier_code?: string
  supplier_name?: string
  snap_price_by_volume?: number
}

/** Một dòng trong thân `POST .../options/assign-supplier` — giá sửa kèm là tùy chọn. */
export interface PrAssignSupplierLine {
  item_id: number
  snap_price_by_volume?: number
}

/**
 * Thân `POST .../options/assign-supplier` — "Áp 1 NCC cho nhiều dòng" (H.10.5):
 * áp một NCC vào PHƯƠNG ÁN ĐANG CHỌN của từng dòng. Cả gói ăn theo nhau — một
 * dòng không hợp lệ (chưa chọn phương án / phương án từ khảo sát) là backend
 * hủy nguyên lô.
 */
export interface PrAssignSupplierPayload {
  supplier_code?: string
  supplier_name?: string
  items: PrAssignSupplierLine[]
}

/** Một đơn mua hàng nháp vừa sinh từ nút gom (H.10.6). */
export interface PrGeneratedOrder {
  id: number
  code: string
  /** Rỗng với đơn gom các dòng chưa có NCC. */
  supplier_code: string
  supplier_name: string
  line_count: number
}

/**
 * Kết quả `POST .../options/generate-orders` (H.10.6): gom dòng đã chọn phương
 * án theo NCC thành N đơn NHÁP một lượt; dòng chưa có NCC gom vào MỘT đơn riêng
 * không NCC (CR-095 chặn ở cửa GỬI DUYỆT, không chặn ở cửa tạo). `skipped` đếm
 * các dòng bị bỏ qua để giao diện nói thành lời thay vì im lặng.
 */
export interface PrGenerateOrdersResult {
  orders: PrGeneratedOrder[]
  skipped: {
    /** Người yêu cầu đã bỏ chọn hết phương án — "khoan mua dòng này". */
    no_chosen: number
    /** Dòng đã nằm trên một đơn mua hàng (kể cả đơn nháp) — chống sinh trùng. */
    already_ordered: number
    cancelled: number
  }
}

/** Thân `PATCH .../options/{oid}` — đúng EDITABLE_FIELDS của backend, không có NCC. */
export interface PrOptionUpdatePayload {
  nstm_note?: string
  snap_price_by_volume?: number
  snap_vat?: number | null
  snap_moq?: number
  snap_quote_unit?: string
  snap_volume_range?: string
  snap_delivery_time?: string
  snap_delivery_place?: string
  snap_shipping_cost?: string
}
