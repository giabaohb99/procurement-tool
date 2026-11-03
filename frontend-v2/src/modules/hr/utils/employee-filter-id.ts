/**
 * Ô lọc nhân sự kiểu "Mọi …" của hộp Cấp quỹ năm và trang Phân bổ hàng loạt (duoc-CR-717).
 *
 * Mốc "không lọc" là CHUỖI riêng, không phải `0`: `0` là id thật "chưa gắn" ở danh mục (bẫy CR-322),
 * còn backend hiểu trường vắng = bỏ qua.
 */
export const FILTER_ANY = 'any'

/** Ô chọn → số gửi backend: "không lọc" / rác / ≤ 0 → `undefined` để bỏ hẳn trường (backend nhận `ge=1`). */
export function toFilterId(value: string): number | undefined {
  const n = Number(value)
  return value !== FILTER_ANY && Number.isInteger(n) && n > 0 ? n : undefined
}
