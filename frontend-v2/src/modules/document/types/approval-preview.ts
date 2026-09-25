/**
 * XEM TRƯỚC LUỒNG DUYỆT — thẻ «Người duyệt dự kiến» (phase 01, duoc-CR-473).
 *
 * Khớp hình dạng `preview_service.preview_flow` bên backend
 * (`POST /api/documents/approval-preview`). CHỈ ĐỌC: gọi API này không mở
 * phiên duyệt nào, người duyệt thực tế chốt lúc gửi duyệt thật.
 */

/**
 * `none` — loại văn bản KHÔNG cần duyệt (`DocType.needs_approval = false`).
 * `flow` — luồng nhiều chặng đang áp.
 * `legacy` — không luồng nào khớp, hoặc bộ máy nhiều bước đang tắt: văn bản sẽ
 * duyệt MỘT BƯỚC kiểu cũ.
 */
export type ApprovalPreviewMode = 'none' | 'flow' | 'legacy'

export interface ApprovalPreviewApprover {
  employee_id: number
  name: string
  /** Chức vụ — rỗng nếu hồ sơ chưa khai. */
  position: string
}

export interface ApprovalPreviewStep {
  seq: number
  name: string
  /** Câu QUY TẮC khai trong luồng, vd «Theo vai trò: Trưởng phòng Nhân sự». */
  rule_label: string
  approvers: ApprovalPreviewApprover[]
  /** Khác rỗng = chặng KHÔNG có ai duyệt và phiếu sẽ DỪNG ở đó nếu gửi ngay. */
  unresolved_reason: string
  /** `true` = `approvers` ở trên là người DỰ PHÒNG, không phải quy tắc gốc. */
  fallback_used: boolean
  /**
   * Chặng kiểu FIELD (vd "người ký") mà ô đó CHƯA CHỌN — tên cột trên phiếu.
   * Rỗng = không phải ca này. Khác `unresolved_reason` ở chỗ đây là chuyện
   * BÌNH THƯỜNG lúc đang soạn, không phải sự cố tổ chức.
   */
  pending_field: string
  /** Ghi chú thêm — vd "chặng này tự động qua vì trùng người ở chặng trước". */
  note: string
}

/** Bước NHẬN BẢN SAO (CC) — không chặn luồng, tách riêng khỏi `steps`. */
export interface ApprovalPreviewCcStep {
  seq: number
  name: string
  rule_label: string
  approvers: ApprovalPreviewApprover[]
}

export interface ApprovalPreviewResult {
  mode: ApprovalPreviewMode
  /** Bộ máy luồng nhiều bước có đang BẬT cho `document` không. */
  engine_enabled: boolean
  flow_name: string
  steps: ApprovalPreviewStep[]
  cc: ApprovalPreviewCcStep[]
}

/**
 * Thân yêu cầu — đúng bộ trường `approval_bridge.entity_context()` trừ `id`
 * (văn bản chưa tồn tại lúc xem trước). `doc_type_id`/`company_id` bắt buộc
 * dương; phần còn lại `0` là "chưa chọn".
 */
export interface ApprovalPreviewInput {
  doc_type_id: number
  company_id: number
  department_id?: number
  secrecy_level?: number
  urgency?: number
  owner_employee_id?: number
  drafter_employee_id?: number
  signer_employee_id?: number
  /** ≠ 0 → xem trước cho BẢN CLONE (pháp nhân con), chỉ xét luồng riêng. */
  source_document_id?: number
}
