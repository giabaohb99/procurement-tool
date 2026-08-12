/**
 * Báo cáo khảo sát — `/api/survey-report/lines`.
 *
 * Mỗi dòng ở đây là MỘT DÒNG bên trong phiếu khảo sát (một NCC được hỏi giá,
 * hoặc một sản phẩm được khảo sát), không phải một phiếu.
 */
export interface SurveyReportLine {
  survey_id: number
  survey_code: string
  /** `supplier` = dòng NCC, `product` = dòng sản phẩm. */
  kind: string
  line_id: number
  /** Nội dung dòng: tên NCC hoặc tên sản phẩm. */
  content: string
  supplier_code: string
  item_group: string
  nspt: string
  item_code: string
  main_content: string
  date: string
  /** Kết quả duyệt của DÒNG — chuỗi tiếng Việt, xem `LINE_APPROVE_STATUSES`. */
  line_approve: string
  line_approve_note: string
  /** Trạng thái của cả phiếu khảo sát (mã tiếng Anh). */
  survey_status: string
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
