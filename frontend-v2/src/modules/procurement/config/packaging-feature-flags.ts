/**
 * duoc-CR-784 — công tắc tạm của cụm Giá bao bì.
 *
 * `PACKAGING_LIMITS_ENABLED`: ngưỡng giá sàn / trần. Người chủ chốt 21/11/2026 "tạm thời chưa xài" nên TẮT: ẩn nút
 * "Ngưỡng" ở Bảng giá VTBB, cột "Sàn – Trần" (Bảng giá + bảng mã đã chọn của màn Tác động) và ô lọc "Chỉ mã ngoài
 * ngưỡng". Backend (`/api/product-price-limits`, cảnh báo vượt ngưỡng) giữ nguyên — bật lại chỉ cần đổi công tắc này.
 */
export const PACKAGING_LIMITS_ENABLED = false

/** Bỏ cột "Sàn – Trần" (khóa `limit`) khi ngưỡng đang tắt; khai kiểu cột tường minh ở nơi gọi để mảng cột giữ kiểu. */
export function dropLimitColumn<T extends { key: string }>(columns: T[]): T[] {
  return PACKAGING_LIMITS_ENABLED ? columns : columns.filter((column) => column.key !== 'limit')
}
