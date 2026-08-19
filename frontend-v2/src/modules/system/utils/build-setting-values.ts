import type { SettingField } from '../types/setting'

/**
 * Gom giá trị gửi lên khi bấm Lưu.
 *
 * LUẬT KHÓA BÍ MẬT — không được nới:
 * - Ô bí mật để TRỐNG nghĩa là "giữ nguyên giá trị cũ", nên KHÔNG gửi khóa đó
 *   lên. Gửi chuỗi rỗng là xóa mất mật khẩu SMTP đang chạy thật.
 * - Chỉ khoảng trắng cũng tính là để trống: người dùng lỡ chạm phím cách trong
 *   ô mật khẩu không được biến thành một lần đổi khóa.
 * - Giá trị người dùng gõ được gửi NGUYÊN VẸN, không trim: mật khẩu ứng dụng của
 *   Google có dạng "abcd efgh ijkl mnop" — trim hai đầu thì được, nhưng cắt bên
 *   trong là hỏng. Ở đây chỉ dùng bản đã trim để QUYẾT ĐỊNH có gửi hay không.
 *
 * Trường thường thì gửi hết, kể cả ô rỗng: rỗng ở đó là "xóa cấu hình", đúng ý
 * người dùng.
 */
export function buildSettingValues(
  fields: SettingField[],
  secretInputs: Record<string, string>,
): Record<string, unknown> {
  const values: Record<string, unknown> = {}

  for (const field of fields) {
    values[field.key] = field.value
  }

  for (const [key, input] of Object.entries(secretInputs)) {
    if (input.trim()) values[key] = input
  }

  return values
}
