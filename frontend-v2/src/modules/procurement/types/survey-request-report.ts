/**
 * Khối BÁO CÁO THỰC HIỆN trên chi tiết phiếu YCBG — `/api/survey-requests/{id}/report`.
 *
 * NS Thu mua theo dõi tiến trình thực thi thương vụ (giấy phép, hợp đồng, chứng
 * từ, thông quan…): hồ sơ chia theo GIAI ĐOẠN, lọc theo NÚT DÒNG HÀNG, mỗi hồ sơ
 * có trạng thái + danh sách hồ sơ tiên quyết (chưa xong hết thì hồ sơ bị khóa).
 */

/** Một NÚT lọc theo dòng hàng (vd «K₂SO₄»). Hồ sơ `item_id = 0` là CHUNG. */
export interface SurveyReportItem {
  id: number
  name: string
  sort_order: number
}

/** Một GIAI ĐOẠN của báo cáo. */
export interface SurveyReportPhase {
  id: number
  name: string
  location: string
  sort_order: number
}

/** Một HỒ SƠ cần hoàn thành. */
export interface SurveyReportDoc {
  id: number
  phase_id: number
  /** 0 = Chung — hiện ở mọi nút dòng hàng. */
  item_id: number
  title: string
  description: string
  required: boolean
  /** Mã SỐ — xem `REPORT_DOC_STATUS_LABELS`. */
  status: number
  status_label: string
  /** Tên tệp hoặc link tài liệu — chữ tự do. */
  file_note: string
  /** Id các hồ sơ TIÊN QUYẾT (backend đã lọc id chết). */
  depends: number[]
  /** Ngày bắt đầu thực hiện — `yyyy-mm-dd`, `''` = chưa đặt. */
  start_date: string
  /** Ngày hết hiệu lực — `yyyy-mm-dd`, `''` = chưa đặt. */
  expires_at: string
  /**
   * Ngày DỰ ĐỊNH HOÀN TẤT (kế hoạch ban đầu, bao-CR-392) — `yyyy-mm-dd`, `''` = chưa
   * đặt. Khác `expires_at` (hạn giấy tờ): qua ngày này mà chưa xong là TRỄ kế hoạch.
   */
  planned_date: string
  /** Nhân sự thực hiện (id `tab_employee`), `0` = chưa cử. */
  assignee_id: number
  /** Tên nhân sự thực hiện — backend resolve, id chết ra `''`. Chỉ đọc. */
  assignee_name: string
  sort_order: number
}

/** `GET /api/survey-requests/{id}/report`. */
export interface SurveyRequestReport {
  items: SurveyReportItem[]
  phases: SurveyReportPhase[]
  docs: SurveyReportDoc[]
  /** Có bản «đã xóa» chưa hoàn tác không — FE hiện nút Hoàn tác. */
  restorable: boolean
  /** Id dòng Lịch sử thao tác của lần xóa gần nhất (để gắn nút Hoàn tác đúng dòng). */
  restorable_audit_id: number
}

//  Bộ mã SỐ gõ tay theo `backend/.../survey_request/report_constants.py` —
//  `gen_status_ts.py` chỉ sinh cho bộ mã CHUỖI (cùng cảnh `hr/types/leave.ts`).
//  Đổi ở backend thì phải nhớ sửa tay bên này.
export const REPORT_DOC_IDLE = 0
export const REPORT_DOC_DOING = 1
export const REPORT_DOC_REVIEW = 2
export const REPORT_DOC_DONE = 3

export const REPORT_DOC_STATUS_LABELS: Record<number, string> = {
  [REPORT_DOC_IDLE]: 'Chưa bắt đầu',
  [REPORT_DOC_DOING]: 'Đang làm',
  [REPORT_DOC_REVIEW]: 'Chờ duyệt',
  [REPORT_DOC_DONE]: 'Hoàn thành',
}
