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

/** Loại mẫu văn bản */
export const DOCUMENT_TEMPLATE_KIND: readonly StatusOption[] = [
  {"value": "1", "label": "Văn bản mẫu", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Mẫu hợp đồng lao động", "sort_order": 2, "is_terminal": false, "is_exception": false},
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

/** Trạng thái hợp đồng lao động */
export const LABOR_CONTRACT_STATUS: readonly StatusOption[] = [
  {"value": "1", "label": "Nháp", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Đã ký – hiệu lực", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Hết hạn", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Đã chấm dứt / thanh lý", "sort_order": 4, "is_terminal": false, "is_exception": false},
  {"value": "5", "label": "Đã hủy", "sort_order": 5, "is_terminal": false, "is_exception": false},
]

/** Loại hợp đồng lao động */
export const LABOR_CONTRACT_TYPE: readonly StatusOption[] = [
  {"value": "1", "label": "Thử việc", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Xác định thời hạn", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Không xác định thời hạn", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Khoán việc / dịch vụ", "sort_order": 4, "is_terminal": false, "is_exception": false},
  {"value": "5", "label": "Cộng tác viên", "sort_order": 5, "is_terminal": false, "is_exception": false},
  {"value": "9", "label": "Khác", "sort_order": 9, "is_terminal": false, "is_exception": false},
]

/** Nguồn biến mẫu hợp đồng lao động */
export const LABOR_CONTRACT_VARIABLE_SOURCE: readonly StatusOption[] = [
  {"value": "1", "label": "Hệ thống", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Tùy chỉnh", "sort_order": 2, "is_terminal": false, "is_exception": false},
]

/** Kiểu giá trị biến mẫu hợp đồng lao động */
export const LABOR_CONTRACT_VARIABLE_TYPE: readonly StatusOption[] = [
  {"value": "1", "label": "Chữ", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Chữ nhiều dòng", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Số", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Ngày", "sort_order": 4, "is_terminal": false, "is_exception": false},
  {"value": "5", "label": "Tiền", "sort_order": 5, "is_terminal": false, "is_exception": false},
]

/** Buổi nghỉ */
export const LEAVE_SESSION: readonly StatusOption[] = [
  {"value": "full", "label": "Cả ngày", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "morning", "label": "Buổi sáng", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "afternoon", "label": "Buổi chiều", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "hourly", "label": "Theo giờ", "sort_order": 0, "is_terminal": false, "is_exception": false},
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
  {"value": "paternity", "label": "Nghỉ vợ sinh con", "sort_order": 0, "is_terminal": false, "is_exception": false},
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

/** Báo cáo */
export const REPORT_KEY: readonly StatusOption[] = [
  {"value": "1", "label": "Báo cáo mua hàng", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Chi tiết YC mua hàng", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Tiến độ báo giá", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Tiến độ mua hàng", "sort_order": 4, "is_terminal": false, "is_exception": false},
  {"value": "5", "label": "Báo cáo khảo sát", "sort_order": 5, "is_terminal": false, "is_exception": false},
  {"value": "6", "label": "Biến động nhân sự", "sort_order": 6, "is_terminal": false, "is_exception": false},
  {"value": "7", "label": "Tình hình nghỉ phép", "sort_order": 7, "is_terminal": false, "is_exception": false},
  {"value": "8", "label": "Quỹ phép năm", "sort_order": 8, "is_terminal": false, "is_exception": false},
  {"value": "9", "label": "Báo cáo đặt xe", "sort_order": 9, "is_terminal": false, "is_exception": false},
  {"value": "10", "label": "Báo cáo đóng dấu", "sort_order": 10, "is_terminal": false, "is_exception": false},
  {"value": "11", "label": "Báo cáo văn bản", "sort_order": 11, "is_terminal": false, "is_exception": false},
  {"value": "12", "label": "Báo cáo phê duyệt", "sort_order": 12, "is_terminal": false, "is_exception": false},
  {"value": "13", "label": "Công việc & Dự án", "sort_order": 13, "is_terminal": false, "is_exception": false},
  {"value": "14", "label": "Hồ sơ cách làm việc", "sort_order": 14, "is_terminal": false, "is_exception": false},
]

/** Loại hình pháp lý NCC */
export const SUPPLIER_LEGAL_TYPE: readonly StatusOption[] = [
  {"value": "company", "label": "Công ty", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "individual", "label": "Cá nhân", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "partnership", "label": "Hợp danh", "sort_order": 0, "is_terminal": false, "is_exception": false},
  {"value": "household", "label": "Hộ kinh doanh", "sort_order": 0, "is_terminal": false, "is_exception": false},
]

/** Chức năng được bấm */
export const UI_ACTION: readonly StatusOption[] = [
  {"value": "1", "label": "Ẩn/hiện cột", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Ghim cột", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Tô màu cột", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Khôi phục bố cục", "sort_order": 4, "is_terminal": false, "is_exception": false},
  {"value": "5", "label": "Sắp xếp", "sort_order": 5, "is_terminal": false, "is_exception": false},
  {"value": "6", "label": "Chuyển trang", "sort_order": 6, "is_terminal": false, "is_exception": false},
  {"value": "7", "label": "Đổi số dòng/trang", "sort_order": 7, "is_terminal": false, "is_exception": false},
  {"value": "8", "label": "Làm mới", "sort_order": 8, "is_terminal": false, "is_exception": false},
  {"value": "9", "label": "Chọn cả trang", "sort_order": 9, "is_terminal": false, "is_exception": false},
  {"value": "20", "label": "Áp bộ lọc", "sort_order": 20, "is_terminal": false, "is_exception": false},
  {"value": "21", "label": "Xóa bộ lọc", "sort_order": 21, "is_terminal": false, "is_exception": false},
  {"value": "22", "label": "Thêm điều kiện lọc", "sort_order": 22, "is_terminal": false, "is_exception": false},
  {"value": "23", "label": "Lọc nhanh", "sort_order": 23, "is_terminal": false, "is_exception": false},
  {"value": "100", "label": "Xuất Excel", "sort_order": 100, "is_terminal": false, "is_exception": false},
  {"value": "101", "label": "In", "sort_order": 101, "is_terminal": false, "is_exception": false},
  {"value": "102", "label": "Xuất báo cáo", "sort_order": 102, "is_terminal": false, "is_exception": false},
  {"value": "200", "label": "Nhân bản phiếu", "sort_order": 200, "is_terminal": false, "is_exception": false},
  {"value": "201", "label": "Sao chép dòng", "sort_order": 201, "is_terminal": false, "is_exception": false},
  {"value": "202", "label": "Xóa nhiều dòng", "sort_order": 202, "is_terminal": false, "is_exception": false},
  {"value": "203", "label": "Tạo mới từ danh sách", "sort_order": 203, "is_terminal": false, "is_exception": false},
]

/** Ứng dụng gửi sự kiện */
export const UI_APP: readonly StatusOption[] = [
  {"value": "1", "label": "ERP v2", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Thu mua (app cũ)", "sort_order": 2, "is_terminal": false, "is_exception": false},
]

/** Loại sự kiện giao diện */
export const UI_EVENT_TYPE: readonly StatusOption[] = [
  {"value": "1", "label": "Xem màn hình", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Rời màn hình", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Mở biểu mẫu", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Gửi biểu mẫu", "sort_order": 4, "is_terminal": false, "is_exception": false},
  {"value": "5", "label": "Bỏ dở biểu mẫu", "sort_order": 5, "is_terminal": false, "is_exception": false},
  {"value": "6", "label": "Tìm kiếm", "sort_order": 6, "is_terminal": false, "is_exception": false},
  {"value": "7", "label": "Lỗi giao diện", "sort_order": 7, "is_terminal": false, "is_exception": false},
  {"value": "8", "label": "Bấm chức năng", "sort_order": 8, "is_terminal": false, "is_exception": false},
]

/** Biểu mẫu có đo */
export const UI_FORM: readonly StatusOption[] = [
  {"value": "1", "label": "Yêu cầu mua hàng", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Yêu cầu báo giá", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Đơn mua hàng", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Đơn nghỉ phép", "sort_order": 4, "is_terminal": false, "is_exception": false},
  {"value": "5", "label": "Hợp đồng lao động", "sort_order": 5, "is_terminal": false, "is_exception": false},
  {"value": "6", "label": "Hồ sơ nhân sự", "sort_order": 6, "is_terminal": false, "is_exception": false},
  {"value": "7", "label": "Yêu cầu thanh toán", "sort_order": 7, "is_terminal": false, "is_exception": false},
  {"value": "8", "label": "Nhận hàng (dòng ĐMH)", "sort_order": 8, "is_terminal": false, "is_exception": false},
  {"value": "9", "label": "Văn bản", "sort_order": 9, "is_terminal": false, "is_exception": false},
  {"value": "10", "label": "Đặt xe", "sort_order": 10, "is_terminal": false, "is_exception": false},
  {"value": "11", "label": "Duyệt dấu", "sort_order": 11, "is_terminal": false, "is_exception": false},
  {"value": "12", "label": "Đặt phòng họp", "sort_order": 12, "is_terminal": false, "is_exception": false},
  {"value": "13", "label": "Việc dự án (tạo nhanh)", "sort_order": 13, "is_terminal": false, "is_exception": false},
]

/** Nhóm so sánh */
export const USAGE_COHORT_KIND: readonly StatusOption[] = [
  {"value": "1", "label": "Cùng vai trò", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Cùng pháp nhân", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Toàn công ty", "sort_order": 3, "is_terminal": false, "is_exception": false},
]

/** Kiểu làm việc */
export const USAGE_STYLE: readonly StatusOption[] = [
  {"value": "1", "label": "Làm dồn", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Nút thắt duyệt", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Dùng Excel song song", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Người mới đang vướng", "sort_order": 4, "is_terminal": false, "is_exception": false},
  {"value": "5", "label": "Người thạo", "sort_order": 5, "is_terminal": false, "is_exception": false},
  {"value": "6", "label": "Hay đi lạc", "sort_order": 6, "is_terminal": false, "is_exception": false},
  {"value": "7", "label": "Làm trên điện thoại", "sort_order": 7, "is_terminal": false, "is_exception": false},
  {"value": "8", "label": "Phiếu kém chất lượng", "sort_order": 8, "is_terminal": false, "is_exception": false},
  {"value": "9", "label": "Nhờ làm hộ", "sort_order": 9, "is_terminal": false, "is_exception": false},
  {"value": "10", "label": "Ít dùng", "sort_order": 10, "is_terminal": false, "is_exception": false},
]

/** Lý do chưa đo được */
export const USAGE_UNMEASURED_REASON: readonly StatusOption[] = [
  {"value": "1", "label": "Chưa thu thập", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Dưới ngưỡng dữ liệu", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Không áp dụng", "sort_order": 3, "is_terminal": false, "is_exception": false},
]

/** Loại ngày làm việc */
export const WORK_DAY_KIND: readonly StatusOption[] = [
  {"value": "1", "label": "Nghỉ", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Cả ngày", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Buổi sáng", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Buổi chiều", "sort_order": 4, "is_terminal": false, "is_exception": false},
]

/** Loại quá trình công tác */
export const WORK_EVENT_TYPE: readonly StatusOption[] = [
  {"value": "1", "label": "Tuyển dụng", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Điều chuyển", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Bổ nhiệm", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Kiêm nhiệm", "sort_order": 4, "is_terminal": false, "is_exception": false},
  {"value": "5", "label": "Miễn nhiệm", "sort_order": 5, "is_terminal": false, "is_exception": false},
  {"value": "6", "label": "Thôi việc", "sort_order": 6, "is_terminal": false, "is_exception": false},
  {"value": "9", "label": "Khác", "sort_order": 9, "is_terminal": false, "is_exception": false},
]

/** Cấp gán lịch làm việc */
export const WORK_SCHEDULE_LEVEL: readonly StatusOption[] = [
  {"value": "1", "label": "Toàn hệ thống", "sort_order": 1, "is_terminal": false, "is_exception": false},
  {"value": "2", "label": "Pháp nhân", "sort_order": 2, "is_terminal": false, "is_exception": false},
  {"value": "3", "label": "Phòng ban", "sort_order": 3, "is_terminal": false, "is_exception": false},
  {"value": "4", "label": "Nhân sự", "sort_order": 4, "is_terminal": false, "is_exception": false},
]

/** Chức năng được bấm — khóa → mã gửi lên backend. */
export const UI_ACTION_CODE = {
  COLUMN_TOGGLE: 1,
  COLUMN_PIN: 2,
  COLUMN_COLOR: 3,
  LAYOUT_RESET: 4,
  SORT_CHANGE: 5,
  PAGE_CHANGE: 6,
  PAGE_SIZE_CHANGE: 7,
  REFRESH: 8,
  SELECT_ALL_PAGE: 9,
  FILTER_APPLY: 20,
  FILTER_RESET: 21,
  FILTER_ROW_ADD: 22,
  QUICK_FILTER: 23,
  EXPORT_EXCEL: 100,
  PRINT: 101,
  REPORT_EXPORT: 102,
  COPY_DOCUMENT: 200,
  COPY_LINE: 201,
  BULK_DELETE_LINES: 202,
  CREATE_NEW: 203,
} as const

/** Ứng dụng gửi sự kiện — khóa → mã gửi lên backend. */
export const UI_APP_CODE = {
  ERP_V2: 1,
  THUMUA: 2,
} as const

/** Loại sự kiện giao diện — khóa → mã gửi lên backend. */
export const UI_EVENT_TYPE_CODE = {
  PAGE_VIEW: 1,
  PAGE_LEAVE: 2,
  FORM_OPEN: 3,
  FORM_SUBMIT: 4,
  FORM_ABANDON: 5,
  SEARCH: 6,
  CLIENT_ERROR: 7,
  UI_ACTION: 8,
} as const

/** Biểu mẫu có đo — khóa → mã gửi lên backend. */
export const UI_FORM_CODE = {
  PURCHASE_REQUEST: 1,
  QUOTE_REQUEST: 2,
  PURCHASE_ORDER: 3,
  LEAVE_REQUEST: 4,
  LABOR_CONTRACT: 5,
  EMPLOYEE_PROFILE: 6,
  PAYMENT_REQUEST: 7,
  GOODS_RECEIPT: 8,
  DOCUMENT: 9,
  VEHICLE_BOOKING: 10,
  SEAL_REQUEST: 11,
  ROOM_BOOKING: 12,
  WORK_TASK: 13,
} as const

/** Tra theo tên bộ, cho chỗ dựng ô chọn động. */
export const STATUS_SETS = {
  contract_expiry: CONTRACT_EXPIRY,
  contract_party_type: CONTRACT_PARTY_TYPE,
  contract_status: CONTRACT_STATUS,
  contract_type: CONTRACT_TYPE,
  document_template_kind: DOCUMENT_TEMPLATE_KIND,
  employee_status: EMPLOYEE_STATUS,
  forum_prefix: FORUM_PREFIX,
  labor_contract_status: LABOR_CONTRACT_STATUS,
  labor_contract_type: LABOR_CONTRACT_TYPE,
  labor_contract_variable_source: LABOR_CONTRACT_VARIABLE_SOURCE,
  labor_contract_variable_type: LABOR_CONTRACT_VARIABLE_TYPE,
  leave_session: LEAVE_SESSION,
  leave_type: LEAVE_TYPE,
  payable_status: PAYABLE_STATUS,
  po_delivery_status: PO_DELIVERY_STATUS,
  po_document_status: PO_DOCUMENT_STATUS,
  po_item_line_status: PO_ITEM_LINE_STATUS,
  po_progress_status: PO_PROGRESS_STATUS,
  pr_line_status: PR_LINE_STATUS,
  report_key: REPORT_KEY,
  supplier_legal_type: SUPPLIER_LEGAL_TYPE,
  ui_action: UI_ACTION,
  ui_app: UI_APP,
  ui_event_type: UI_EVENT_TYPE,
  ui_form: UI_FORM,
  usage_cohort_kind: USAGE_COHORT_KIND,
  usage_style: USAGE_STYLE,
  usage_unmeasured_reason: USAGE_UNMEASURED_REASON,
  work_day_kind: WORK_DAY_KIND,
  work_event_type: WORK_EVENT_TYPE,
  work_schedule_level: WORK_SCHEDULE_LEVEL,
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
