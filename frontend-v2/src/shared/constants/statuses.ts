// TỆP SINH TỰ ĐỘNG — ĐỪNG SỬA TAY.
// Nguồn: backend/app/core/status_catalog.py (sổ đăng ký nạp qua app/core/code_sets.py).
// Sinh lại: docker compose exec -T api python -m scripts.gen_status_ts
// Sửa nhãn hay thêm mã thì sửa ở Python rồi sinh lại, đừng vá ở đây — CI so hai bên,
// lệch một ký tự là hỏng build.

export interface StatusOption {
  /** MÃ lưu trong CSDL. Không bao giờ đổi. */
  value: string
  /** Nhãn tiếng Việt để hiển thị. Đổi thoải mái. */
  label: string
  /** Vị trí trong chuỗi tiến trình. Bộ không có thứ tự thì mọi mã đều là 0. */
  sort_order: number
  /** Trạng thái kết, không đi tiếp được. */
  is_terminal: boolean
  /** Nhánh rẽ ra khỏi chuỗi (tạm ngưng, hủy) — không có chỗ trong thứ tự. */
  is_exception: boolean
}

/** Tình trạng hạn hợp đồng */
export const CONTRACT_EXPIRY: readonly StatusOption[] = [
  {"value": "valid", "label": "Còn hạn", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "expiring_soon", "label": "Sắp hết hạn", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "expired", "label": "Hết hạn", "sort_order": 3, "is_terminal": true, "is_exception": false},
]

/** Loại đối tượng */
export const CONTRACT_PARTY_TYPE: readonly StatusOption[] = [
  {"value": "supplier", "label": "Nhà cung cấp", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "customer", "label": "Khách hàng", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "other", "label": "Khác", "sort_order": 0, "is_terminal": false, "is_exception": false},
]

/** Trạng thái hợp đồng */
export const CONTRACT_STATUS: readonly StatusOption[] = [
  {"value": "active", "label": "Hiệu lực", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "expired", "label": "Hết hạn", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "liquidated", "label": "Thanh lý", "sort_order": 3, "is_terminal": true, "is_exception": false},
  {"value": "cancelled", "label": "Hủy", "sort_order": 0, "is_terminal": false, "is_exception": true},
]

/** Loại hợp đồng */
export const CONTRACT_TYPE: readonly StatusOption[] = [
  {"value": "purchase", "label": "Hợp đồng mua bán", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "principle", "label": "Hợp đồng nguyên tắc", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "economic", "label": "Hợp đồng kinh tế", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "template", "label": "Hợp đồng khuôn mẫu", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "transport", "label": "Hợp đồng vận chuyển", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "service", "label": "Hợp đồng dịch vụ", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "other", "label": "Khác", "sort_order": 0, "is_terminal": false, "is_exception": false},
]

/** Trạng thái nhân sự */
export const EMPLOYEE_STATUS: readonly StatusOption[] = [
  {"value": "official", "label": "Chính thức", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "collaborator", "label": "Cộng tác viên", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "maternity_leave", "label": "Nghỉ thai sản", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "resigned", "label": "Nghỉ việc", "sort_order": 0, "is_terminal": false, "is_exception": false},
]

/** Prefix chủ đề diễn đàn */
export const FORUM_PREFIX: readonly StatusOption[] = [
  {"value": "0", "label": "Không prefix", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "1", "label": "Thảo luận", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Thắc mắc", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Kiến thức", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Khoe", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "5", "label": "Đánh giá", "sort_order": 0, "is_terminal": false, "is_exception": false},
]

/** Buổi nghỉ */
export const LEAVE_SESSION: readonly StatusOption[] = [
  {"value": "full", "label": "Cả ngày", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "morning", "label": "Buổi sáng", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "afternoon", "label": "Buổi chiều", "sort_order": 0, "is_terminal": false, "is_exception": false},
]

/** Loại nghỉ phép */
export const LEAVE_TYPE: readonly StatusOption[] = [
  {"value": "annual", "label": "Phép năm", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "unpaid", "label": "Nghỉ không lương", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "sick", "label": "Nghỉ ốm đau", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "maternity", "label": "Nghỉ thai sản", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "wedding", "label": "Nghỉ cưới hỏi", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "funeral", "label": "Nghỉ tang chế", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "comp_off", "label": "Nghỉ bù", "sort_order": 0, "is_terminal": false, "is_exception": false},
]

/** Trạng thái công nợ */
export const PAYABLE_STATUS: readonly StatusOption[] = [
  {"value": "unpaid", "label": "Chờ thanh toán", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "partial", "label": "Thanh toán một phần", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "paid", "label": "Đã thanh toán", "sort_order": 3, "is_terminal": false, "is_exception": false},
]

/** Trạng thái lần giao */
export const PO_DELIVERY_STATUS: readonly StatusOption[] = [
  {"value": "pending", "label": "Chờ giao", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "short", "label": "Giao thiếu", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "defect", "label": "Lỗi", "sort_order": 3, "is_terminal": false, "is_exception": true},
  {"value": "received", "label": "Đã nhận", "sort_order": 4, "is_terminal": false, "is_exception": false},
]

/** Hồ sơ chứng từ đơn mua hàng */
export const PO_DOCUMENT_STATUS: readonly StatusOption[] = [
  {"value": "none", "label": "Chưa có chứng từ", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "partial", "label": "Đã có thông tin chứng từ", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "full", "label": "Đã đủ chứng từ", "sort_order": 3, "is_terminal": true, "is_exception": false},
]

/** Trạng thái giao của dòng đơn mua hàng */
export const PO_ITEM_LINE_STATUS: readonly StatusOption[] = [
  {"value": "not_delivered", "label": "Chưa giao", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "partial", "label": "Đang giao", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "full", "label": "Đủ", "sort_order": 3, "is_terminal": false, "is_exception": false},
]

/** Tiến độ dòng đơn mua hàng */
export const PO_PROGRESS_STATUS: readonly StatusOption[] = [
  {"value": "not_ordered", "label": "Chưa đặt hàng", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "ordered", "label": "Đã đặt hàng", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "received", "label": "Đã nhận hàng", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "doc_pending", "label": "Chưa gửi ĐMH cho KT", "sort_order": 4, "is_terminal": false, "is_exception": false},
  {"value": "doc_sent", "label": "Đã gửi ĐMH cho KT", "sort_order": 5, "is_terminal": false, "is_exception": false},
  {"value": "completed", "label": "Hoàn thành", "sort_order": 6, "is_terminal": true, "is_exception": false},
  {"value": "paused", "label": "Tạm ngưng", "sort_order": 0, "is_terminal": false, "is_exception": true},
  {"value": "cancelled", "label": "Hủy đơn", "sort_order": 0, "is_terminal": true, "is_exception": true},
]

/** Trạng thái dòng Yêu cầu mua hàng */
export const PR_LINE_STATUS: readonly StatusOption[] = [
  {"value": "no_po", "label": "Chưa tạo đơn mua hàng", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "not_ordered", "label": "Chưa đặt hàng", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "ordered", "label": "Đã đặt hàng", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "received", "label": "Đã nhận hàng", "sort_order": 4, "is_terminal": false, "is_exception": false},
  {"value": "completed", "label": "Hoàn thành", "sort_order": 5, "is_terminal": true, "is_exception": false},
  {"value": "cancelled", "label": "Hủy đơn", "sort_order": 0, "is_terminal": true, "is_exception": true},
]

/** Loại hình pháp lý NCC */
export const SUPPLIER_LEGAL_TYPE: readonly StatusOption[] = [
  {"value": "company", "label": "Công ty", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "individual", "label": "Cá nhân", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "partnership", "label": "Hợp danh", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "household", "label": "Hộ kinh doanh", "sort_order": 0, "is_terminal": false, "is_exception": false},
]

/** Kết quả duyệt phiếu khảo sát */
export const SURVEY_APPROVE_STATUS: readonly StatusOption[] = [
  {"value": "pending", "label": "Chưa xét duyệt", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "approved", "label": "Duyệt", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "rejected", "label": "Không duyệt", "sort_order": 0, "is_terminal": false, "is_exception": false},
]

/** Tra theo tên bộ, cho chỗ dựng ô chọn động. */
export const STATUS_SETS = {
  contract_expiry: CONTRACT_EXPIRY,
  contract_party_type: CONTRACT_PARTY_TYPE,
  contract_status: CONTRACT_STATUS,
  contract_type: CONTRACT_TYPE,
  employee_status: EMPLOYEE_STATUS,
  forum_prefix: FORUM_PREFIX,
  leave_session: LEAVE_SESSION,
  leave_type: LEAVE_TYPE,
  payable_status: PAYABLE_STATUS,
  po_delivery_status: PO_DELIVERY_STATUS,
  po_document_status: PO_DOCUMENT_STATUS,
  po_item_line_status: PO_ITEM_LINE_STATUS,
  po_progress_status: PO_PROGRESS_STATUS,
  pr_line_status: PR_LINE_STATUS,
  supplier_legal_type: SUPPLIER_LEGAL_TYPE,
  survey_approve_status: SURVEY_APPROVE_STATUS,
} as const

/** Nhãn theo mã, cho chỗ chỉ cần hiển thị. */
export function labelOf(options: readonly StatusOption[], value: string | null | undefined): string {
  return options.find((o) => o.value === value)?.label ?? ''
}

/** Chuỗi tiến trình theo sort_order, đã bỏ các mã ngoại lệ. */
export function orderedValues(options: readonly StatusOption[]): string[] {
  return options.filter((o) => !o.is_exception)
    .slice()
    .sort((a, b) => a.sort_order - b.sort_order)
    .map((o) => o.value)
}
