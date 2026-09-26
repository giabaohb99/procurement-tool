// bao-CR-496 — kiểu dữ liệu của bộ lọc đã lưu và nhật ký từng dòng của lô nạp hải quan.

/** Một bộ lọc người dùng đặt tên (`/api/customs/saved-filters`) — riêng từng tài khoản. */
export interface CustomsSavedFilter {
  id: number
  name: string
  /** Chuỗi tham số URL của trang tra cứu (`q=…&hs_code=…`), giữ nguyên, không tách cột. */
  params: string
  /** Chưa dùng — cột chừa sẵn để sau mở «bộ lọc chung». */
  is_shared: boolean
  updated_at: string | null
}

export interface CustomsSavedFilterList {
  items: CustomsSavedFilter[]
  max_per_user: number
}

/** Kết cục của một dòng dữ liệu trong tệp — khớp `ImportRowStatus` của backend (luật R2). */
export const CUSTOMS_ROW_STATUS = {
  NEW: 1,
  ERROR: 2,
  DUPLICATE: 3,
} as const

export type CustomsRowStatus = (typeof CUSTOMS_ROW_STATUS)[keyof typeof CUSTOMS_ROW_STATUS]

/** Một dòng của `/api/customs/imports/{id}/rows`. */
export interface CustomsBatchRow {
  id: number
  row_no: number
  row_status: number
  row_status_label: string
  product_name: string
  message: string
}

export interface CustomsBatchRowList {
  total: number
  items: CustomsBatchRow[]
  page: number
  page_size: number
}

/** Tổng theo kết cục của một lô (`/rows/summary`). */
export interface CustomsBatchRowSummary {
  total: number
  new: number
  error: number
  duplicate: number
  labels: Record<string, string>
}
