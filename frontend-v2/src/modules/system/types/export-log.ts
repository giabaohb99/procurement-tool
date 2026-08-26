/** Kiểu dữ liệu phân hệ Xuất dữ liệu (Đ-13b) — khớp `export_log/controller.py`. */

export interface ExportLog {
  id: number
  /** Khóa đối tượng (employee/department/company…). */
  entity: string
  /** Nhãn tiếng Việt của đối tượng. */
  entity_label: string
  /** Phân hệ chứa bảng (hr/procurement/…). */
  module?: string
  /** csv | xlsx. */
  fmt: string
  row_count: number
  filename: string
  file_size: number | null
  /** Có file đã lưu để tải lại ở trang chi tiết không. */
  has_file?: boolean
  filter_summary: string | null
  created_at: string
  created_by: number | null
  created_by_name: string | null
}

/** Một đối tượng người dùng được phép xuất — đổ vào ô chọn của hộp thoại. */
export interface ExportEntityOption {
  entity: string
  label: string
  /** Phân hệ chứa bảng này (hr, procurement…) — để gom nhóm khi chọn. */
  module: string
}

export interface ExportListResponse {
  total: number
  items: ExportLog[]
  creators: string[]
}
