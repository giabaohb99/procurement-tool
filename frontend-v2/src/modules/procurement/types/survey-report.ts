/**
 * Báo cáo khảo sát — `/api/survey-report/lines`.
 *
 * Mỗi dòng ở đây là MỘT DÒNG bên trong phiếu khảo sát (một NCC được hỏi giá,
 * hoặc một sản phẩm được khảo sát), không phải một phiếu.
 *
 * ⚠️ Dòng NCC và dòng SP có tập trường lệch nhau gần hết, nhưng backend
 * (`survey/service.py::report_rows`) vẫn trả ĐỦ bộ khóa cho cả hai loại: loại
 * nào không có thì chuỗi rỗng, còn cột số thì `null`. Nên đọc trường của loại
 * kia không nổ, chỉ ra ô trắng — đừng thêm `?` vào các khóa dưới đây.
 */
export interface SurveyReportLine {
  survey_id: number
  survey_code: string
  /** `supplier` = dòng NCC, `product` = dòng sản phẩm. */
  kind: string
  line_id: number
  /** Nội dung dòng: tên NCC hoặc tên sản phẩm. */
  content: string
  /** Ngày đại diện của dòng: ngày liên hệ, thiếu thì lấy ngày tiếp nhận phiếu. */
  date: string
  /** Kết quả duyệt của DÒNG — chuỗi tiếng Việt, xem `LINE_APPROVE_STATUSES`. */
  line_approve: string
  line_approve_note: string
  /** Trạng thái của cả phiếu khảo sát (mã tiếng Anh). */
  survey_status: string

  // ── Header phiếu (lặp lại y hệt trên mọi dòng của cùng một phiếu) ──
  /** `supplier` = khảo sát NCC, `product` = khảo sát SP. */
  survey_type: string
  sr_code: string
  pr_code: string
  item_group: string
  nspt: string
  item_code: string
  item_name: string
  uom: string
  main_content: string
  requirement_detail: string
  received_date: string
  result_due_date: string
  request_qty: number | null
  proposed_rate: number | null

  // ── Ngày của dòng (cả hai loại) ──
  contact_date: string
  reply_date: string
  result_date: string

  // ── Dòng NCC ──
  supplier_code: string
  supplier_name: string
  tax_code: string
  contact_person: string
  contact_phone: string
  supply_group: string
  source_of_information: string
  production_time: string
  nvkd_eval: string
  invoice_policy: string
  reliability: string
  delivery_policy: string
  defect_return: string

  // ── Dòng SP ──
  internal_code: string
  invoice_name: string
  spec: string
  active_ingredient: string
  origin: string
  quote_unit: string
  volume_range: string
  shipping_policy: string
  delivery_time: string
  delivery_place: string
  /** `"Có"` hoặc rỗng — backend quy cờ true/false về chữ để cột này xuất CSV như mọi cột chữ. */
  sample_ready: string
  sample_date: string
  lab_result: string
  moq: number | null
  price_by_volume: number | null
  last_purchase_price: number | null
  max_purchase_price: number | null
  vat: number | null
  amount: number | null
  shipping_cost: number | null
  extra_shipping_cost: number | null
  sample_qty: number | null

  // ── Chung hai loại ──
  debt_policy: string
  nspt_note: string
  note: string
}

/** Bốn ô đếm ở đầu trang; backend tính TRƯỚC khi lọc theo trạng thái. */
export type SurveyReportSummary = Record<(typeof LINE_APPROVE_STATUSES)[number], number>

export interface SurveyReportResult {
  total: number
  items: SurveyReportLine[]
  summary: SurveyReportSummary
}

export const LINE_APPROVE_STATUSES = [
  'Chờ duyệt',
  'Đã duyệt',
  'Không duyệt',
  'Thiếu thông tin',
] as const
