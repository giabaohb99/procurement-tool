/**
 * Kiểu dữ liệu cho phân hệ Quản lý Import (nạp dữ liệu hàng loạt từ tệp Excel).
 *
 * Khớp phong bì backend `app/modules/import_tool/controller.py` (`_batch_out`,
 * `_log_out`). Backend chưa có Pydantic schema riêng — output là dict thủ công —
 * nên các trường ở đây là bản đối chiếu tay, sửa backend thì sửa cả file này.
 */

/** Một lần import (batch). Các số enum tra nhãn ở `config/import-meta.ts`. */
export interface ImportBatch {
  id: number
  /** Đối tượng nhập: 1 = Khảo sát · 2 = Đơn mua hàng. */
  module: number
  /** Chế độ: 0 = Chạy thử (dry-run) · 1 = Ghi thật. */
  mode: number
  filename: string
  file_id: number | null
  file_size: number | null
  /** 0 Chờ · 1 Đang chạy · 2 Xong · 3 Lỗi · 4 Đã hoàn tác. */
  status: number
  /** JSON số dòng mỗi sheet (chuỗi). */
  sheet_info: string | null
  total_rows: number
  created_count: number
  updated_count: number
  deleted_count: number
  skipped_count: number
  warning_count: number
  error_count: number
  review_count: number
  error_summary: string | null
  created_at: string
  created_by: number | null
  created_by_name: string | null
  started_at: string | null
  finished_at: string | null
}

/** Một dòng nhật ký import (mức Info/Cảnh báo/Rà soát/Lỗi cho từng dòng file). */
export interface ImportLog {
  id: number
  sheet: string | null
  row_no: number | null
  /** 0 Info · 1 Cảnh báo · 2 Rà soát · 3 Lỗi. */
  level: number
  category: string | null
  message: string | null
  /** Mã tham chiếu ở file gốc (Mã YC / MST / Số HĐ…). */
  ref_key: string | null
  /** Mã bản ghi đã tạo/sửa (KS##### / PO#####). */
  target_code: string | null
}

export interface ImportListResponse {
  total: number
  items: ImportBatch[]
  /** Danh sách tên người từng import — đổ vào bộ lọc "Người nhập". */
  creators: string[]
}

export interface ImportLogListResponse {
  total: number
  items: ImportLog[]
}
