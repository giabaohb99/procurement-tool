import { z } from 'zod'

/**
 * Ràng buộc form của ba danh mục phụ. Gom một file vì cả ba đều ngắn và luôn
 * được sửa cùng nhau khi đổi mô hình dữ liệu.
 */

/** Mã danh mục: chữ HOA không dấu, số và gạch ngang. */
const CODE_PATTERN = /^[A-Z0-9-]+$/
/** Khóa trường động: chữ thường không dấu, số và gạch dưới. */
const FIELD_CODE_PATTERN = /^[a-z][a-z0-9_]*$/

const codeField = z
  .string()
  .trim()
  .min(1, 'Nhập mã')
  .max(20, 'Mã tối đa 20 ký tự')
  .regex(CODE_PATTERN, 'Chỉ dùng chữ HOA không dấu, số và dấu gạch ngang')

// ===== Mức mật / khẩn =====
export const securityLevelSchema = z.object({
  code: codeField,
  name: z.string().trim().min(1, 'Nhập tên mức').max(60, 'Tên tối đa 60 ký tự'),
  kind: z.enum(['confidential', 'urgent']),
  rank: z.coerce.number().int().min(0, 'Thứ bậc từ 0 trở lên').max(9, 'Thứ bậc tối đa 9'),
  description: z.string().trim().max(255, 'Mô tả tối đa 255 ký tự'),
  is_active: z.boolean(),
})
export type SecurityLevelFormValues = z.infer<typeof securityLevelSchema>

// ===== Đối tác =====
export const documentPartnerSchema = z.object({
  code: codeField,
  name: z.string().trim().min(1, 'Nhập tên đối tác').max(160, 'Tên tối đa 160 ký tự'),
  kind: z.enum(['agency', 'company', 'individual', 'internal']),
  contact_person: z.string().trim().max(120, 'Tối đa 120 ký tự'),
  phone: z.string().trim().max(40, 'Tối đa 40 ký tự'),
  email: z.union([z.literal(''), z.string().trim().email('Email không hợp lệ')]),
  address: z.string().trim().max(255, 'Tối đa 255 ký tự'),
  is_active: z.boolean(),
})
export type DocumentPartnerFormValues = z.infer<typeof documentPartnerSchema>

// ===== Trường thông tin động =====
export const dynamicFieldSchema = z
  .object({
    code: z
      .string()
      .trim()
      .min(1, 'Nhập khóa trường')
      .max(40, 'Khóa tối đa 40 ký tự')
      .regex(FIELD_CODE_PATTERN, 'Chữ thường không dấu, số và gạch dưới; bắt đầu bằng chữ'),
    label: z.string().trim().min(1, 'Nhập nhãn hiển thị').max(120, 'Tối đa 120 ký tự'),
    field_type: z.enum(['text', 'textarea', 'number', 'date', 'select', 'checkbox']),
    /** Nhập mỗi dòng một lựa chọn; tách chuỗi khi lưu. */
    options_text: z.string(),
    is_required: z.boolean(),
    document_type_ids: z.array(z.number()),
    help_text: z.string().trim().max(255, 'Tối đa 255 ký tự'),
    sort_order: z.coerce.number().int().min(0).max(999),
    is_active: z.boolean(),
  })
  // Kiểu "chọn từ danh sách" mà không có lựa chọn nào thì người nhập văn bản
  // nhìn thấy một ô select rỗng, không hiểu phải làm gì.
  .refine(
    (values) =>
      values.field_type !== 'select' ||
      values.options_text.split('\n').some((line) => line.trim()),
    { path: ['options_text'], message: 'Nhập ít nhất một lựa chọn' },
  )
export type DynamicFieldFormValues = z.infer<typeof dynamicFieldSchema>
