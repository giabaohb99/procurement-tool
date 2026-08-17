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
  todo: DocumentTodo[]
  recent: DocumentRecord[]
  year: number
}
