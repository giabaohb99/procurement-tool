import type { DocumentRecord } from './document-record'

/** Số liệu trang tổng quan Văn thư — một lần gọi trả đủ cả trang. */

export interface DocumentDashboardKpi {
  effective: number
  submitted: number
  /** Cờ do E07/E08/F11 bật — văn bản cha đã đổi hoặc bị bãi bỏ. */
  needs_review: number
  /** Hết hiệu lực trong 30 ngày tới. */
  expiring: number
  draft: number
}

export interface MonthlyPoint {
  label: string
  value: number
}

export interface TypeShare {
  name: string
  value: number
}

/**
 * MA TRẬN ƯU TIÊN — văn bản còn hiệu lực chia bốn ô *quan trọng × khẩn cấp*.
 *
 * Hai trục lấy từ hai chỗ khác nhau:
 * - **khẩn cấp** = `urgency` của từng văn bản (2 Khẩn · 3 Hỏa tốc);
 * - **quan trọng** = cờ của LOẠI (cần duyệt / cần QĐ ban hành) — bảng văn bản
 *   không có cột "quan trọng" nào, nên hai văn bản cùng loại luôn cùng một nửa.
 */
export interface PriorityMatrix {
  important_urgent: number
  important_normal: number
  normal_urgent: number
  normal_normal: number
}

export interface DocumentTodo {
  key: string
  label: string
  hint: string
  count: number
  tone: 'warning' | 'default'
}

export interface DocumentDashboard {
  kpi: DocumentDashboardKpi
  issued_12m: MonthlyPoint[]
  by_type: TypeShare[]
  priority_matrix: PriorityMatrix
  todo: DocumentTodo[]
  recent: DocumentRecord[]
  year: number
}
