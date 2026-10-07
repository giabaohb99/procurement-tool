/**
 * Kiểu dữ liệu của tính năng HỢP ĐỒNG LAO ĐỘNG (HĐLĐ) — gồm cả Mẫu hợp đồng
 * (phase 03) lẫn bản ghi hợp đồng của từng nhân sự (phase 04).
 *
 * Bộ mã SỐ `contract_type` / `status` lấy từ `LABOR_CONTRACT_TYPE` /
 * `LABOR_CONTRACT_STATUS` trong `@/shared/constants/statuses` (sinh từ backend):
 * đừng gõ lại danh sách nhãn ở đây.
 */

/** Một biến dùng được trong mẫu .docx — danh mục do BACKEND giữ, FE chỉ đọc. */
export interface LaborContractPlaceholder {
  key: string
  label: string
  group: string
  example: string
}

/** Mẫu hợp đồng của MỘT pháp nhân (mỗi mẫu đúng một loại HĐ). */
export interface LaborContractTemplate {
  id: number
  company_id: number
  company_name: string
  /** Mã pháp nhân (ưu tiên mã phát hành) — phân biệt hai pháp nhân trùng tên. */
  company_code: string
  contract_type: number
  name: string
  note: string
  original_filename: string
  file_size: number
  /** Các biến mẫu đang dùng (backend quét lúc tải lên). */
  placeholders: string[]
  is_active: boolean
  created_at: string
  created_by_name: string
  /** Số HĐ đã tham chiếu mẫu — gom 1 truy vấn cho cả trang. */
  contract_count: number
}

/** Giá trị nhập của hộp tải lên mẫu (chưa kèm tệp). */
export interface LaborContractTemplateFormValues {
  name: string
  /** 0 = chưa chọn — chặn trước khi gửi. */
  company_id: number
  /** 0 = chưa chọn — backend cũng trả 422. */
  contract_type: number
  note: string
}

/** Sửa thông tin mẫu: KHÔNG đổi được pháp nhân. */
export interface LaborContractTemplateUpdatePayload {
  name?: string
  note?: string
  contract_type?: number
  is_active?: boolean
}

/**
 * Nội dung mẫu để SOẠN TRÊN WEB (duoc-CR-606): tệp .docx mở ra HTML + lề trái / phải (mm) của bản
 * gốc. Lưu lại cùng hình dạng — backend dựng .docx rồi kiểm biến như lúc tải tệp lên.
 */
export interface LaborContractTemplateContent {
  html: string
  margin_left_mm: number
  margin_right_mm: number
}

/** Mẫu hiện trong ô chọn ở tab «Hợp đồng» của hồ sơ — chỉ id/tên/loại. */
export interface LaborContractTemplateOption {
  id: number
  name: string
  contract_type: number
}

/**
 * Một hợp đồng lao động — khớp `LaborContractOut` của backend. Cờ `can_*` và
 * `transitions` do BACKEND tính (A9), FE không tự ghép từ `can()`.
 */
export interface LaborContract {
  id: number
  /** Mã hệ thống (backend sinh). */
  code: string
  /** Số HĐ do người dùng gõ; có thể rỗng. */
  contract_no: string
  employee_id: number
  company_id: number
  company_name: string
  department_id: number
  department_name: string
  template_id: number
  template_name: string
  contract_type: number
  /** Trạng thái LƯU trong DB. */
  status: number
  /** Trạng thái hiển thị — thêm «Hết hạn» (3, suy ra theo ngày, không lưu). */
  effective_status: number
  sign_date: string | null
  start_date: string
  end_date: string | null
  job_title: string
  work_location: string
  base_salary: number
  insurance_salary: number
  /** Phụ cấp = MỘT số tiền + ghi chú (không có bảng con). */
  allowance: number
  allowance_note: string
  note: string
  has_generated_file: boolean
  generated_at: string | null
  has_signed_file: boolean
  terminated_date: string | null
  terminate_reason: string
  created_at: string | null
  created_by_name: string
  can_edit: boolean
  can_delete: boolean
  can_generate: boolean
  /** Có quyền `print` trong phạm vi VÀ đã có tệp sinh. */
  can_print: boolean
  can_upload_signed: boolean
  /** Mã trạng thái ĐÍCH chuyển được (DRAFT -> [2,5]; SIGNED -> [4]). */
  transitions: number[]
}

/** Kết quả `GET /api/employees/{id}/labor-contracts`. */
export interface LaborContractListResult {
  items: LaborContract[]
  /** Chỉ là gợi ý — chốt thật ở POST. */
  can_create: boolean
}

/** Kết quả tạo / sửa: `warnings` không chặn (vd HĐ xác định thời hạn > 36 tháng). */
export interface LaborContractSaveResult {
  item: LaborContract
  warnings: string[]
}

/** Nội dung TẠO hợp đồng. `job_title` / `work_location` rỗng -> backend lấy từ hồ sơ. */
export interface LaborContractPayload {
  contract_type: number
  contract_no: string
  start_date: string
  end_date: string | null
  job_title: string | null
  work_location: string | null
  base_salary: number
  insurance_salary: number
  allowance: number
  allowance_note: string
  note: string
}

/** PATCH: trường vắng/null bị bỏ qua, riêng `end_date: null` là GỠ ngày kết thúc. */
export type LaborContractUpdatePayload = Partial<LaborContractPayload>

export interface LaborContractGeneratePayload {
  template_id: number
}

export interface LaborContractTransitionPayload {
  to_status: number
  /** Ngày ký (->2) hoặc ngày chấm dứt (->4). */
  date?: string | null
  /** Bắt buộc cho ->5 (hủy) và ->4 (chấm dứt). */
  reason?: string
}
