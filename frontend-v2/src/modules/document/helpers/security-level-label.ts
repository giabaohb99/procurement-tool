import {
  FALLBACK_CONFIDENTIAL_LEVELS,
  FALLBACK_URGENCY_LEVELS,
  SECURITY_LEVEL_KIND_CONFIDENTIAL,
  type SecurityLevel,
  type SecurityLevelKind,
} from '../types/security-level'

/**
 * Tra TÊN của một bậc theo con số nằm trên văn bản.
 *
 * ⚠️ Tra theo `(kind, value)`, KHÔNG theo `id`. `id` là khóa chính tự tăng, còn
 * `value` mới là con số lưu ở `tab_document.secrecy_level` / `.urgency`. Hai số
 * này chỉ tình cờ trùng nhau ở bảy dòng seed gốc — thêm một bậc mới là chúng
 * lệch ngay, và tra nhầm thì văn bản mức Mật hiện ra tên của một mức khác. Sai
 * âm thầm: không lỗi, không cảnh báo.
 *
 * Thứ tự tìm:
 *  1. danh mục thật (đã nạp từ API);
 *  2. bản dự phòng — cho lúc chưa nạp xong hoặc chỗ gọi không có hook;
 *  3. chính con số đó. Trả chuỗi rỗng là cột trong bảng trống trơn, người đọc
 *     không biết là "không có mức" hay "chưa tải xong".
 */
export function securityLevelLabel(
  items: SecurityLevel[],
  kind: SecurityLevelKind,
  value: number | null | undefined,
): string {
  if (value === null || value === undefined) return ''

  const found = items.find((item) => item.kind === kind && item.value === value)
  if (found) return found.name

  const duPhong = (
    kind === SECURITY_LEVEL_KIND_CONFIDENTIAL
      ? FALLBACK_CONFIDENTIAL_LEVELS
      : FALLBACK_URGENCY_LEVELS
  ).find((item) => item.value === value)

  return duPhong?.name ?? String(value)
}
