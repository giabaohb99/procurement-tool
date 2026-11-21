/**
 * duoc-CR-784 — công tắc tạm của cụm Giá bao bì (bản giao diện cũ; bản v2 ở
 * `frontend-v2/src/modules/procurement/config/packaging-feature-flags.ts`, giữ hai bản cùng giá trị).
 *
 * `PACKAGING_LIMITS_ENABLED`: ngưỡng giá sàn / trần. Người chủ chốt 21/11/2026 "tạm thời chưa xài" nên TẮT: ẩn nút
 * "Ngưỡng", cột "Sàn – Trần" và ô lọc "Chỉ mã ngoài ngưỡng". Backend giữ nguyên — bật lại chỉ cần đổi công tắc này.
 */
export const PACKAGING_LIMITS_ENABLED = false
