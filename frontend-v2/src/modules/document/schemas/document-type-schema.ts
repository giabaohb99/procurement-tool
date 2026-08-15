import { z } from 'zod'

/**
 * Ràng buộc form Loại văn bản.
 *
 * `code` chỉ cho chữ HOA không dấu, số và gạch ngang: nó **đi thẳng vào số hiệu
 * văn bản** (`TB-2026-001`), có dấu tiếng Việt hay khoảng trắng là hỏng cả chuỗi
 * mã — mà số hiệu đã ban hành thì không sửa được nữa.
 */
const CODE_PATTERN = /^[A-Z0-9-]+$/

export const documentTypeSchema = z.object({
  code: z
    .string()
    .trim()
    .min(1, 'Nhập mã loại')
    .max(10, 'Mã tối đa 10 ký tự')
    .regex(CODE_PATTERN, 'Chỉ dùng chữ HOA không dấu, số và dấu gạch ngang'),
  name: z.string().trim().min(1, 'Nhập tên loại văn bản').max(200, 'Tên tối đa 200 ký tự'),
  group_code: z.string().trim().max(1),
  description: z.string().trim().max(1000, 'Mô tả tối đa 1000 ký tự'),

  id_scheme: z.union([z.literal(1), z.literal(2)]),
  number_when: z.union([z.literal(1), z.literal(2)]),
  default_secrecy: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4)]),

  // Chu kỳ rà soát / thời hạn lưu tính bằng THÁNG. 0 = không đặt.
  review_cycle_months: z.coerce
    .number()
    .int('Nhập số nguyên')
    .min(0, 'Không âm')
    .max(600, 'Tối đa 600 tháng'),
  retention_months: z.coerce
    .number()
    .int('Nhập số nguyên')
    .min(0, 'Không âm')
    .max(1200, 'Tối đa 1200 tháng'),

  needs_approval: z.boolean(),
  needs_signature: z.boolean(),
  needs_decision: z.boolean(),
  is_confidential_type: z.boolean(),

  is_active: z.boolean(),
})

export type DocumentTypeFormValues = z.infer<typeof documentTypeSchema>
