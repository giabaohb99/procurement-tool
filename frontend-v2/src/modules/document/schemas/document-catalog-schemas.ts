import { z } from 'zod'

/**
 * Ràng buộc form của danh mục ĐƠN VỊ GỬI NHẬN.
 *
 * Trước đây tệp này còn schema của mức mật/khẩn và trường thông tin động; cả hai
 * đã bỏ: mức mật nay là thang cố định khai trong mã (`types/security-level.ts`),
 * còn trường động bỏ khỏi bản 1 vì soạn thảo gõ thẳng trên web.
 */

/** Mã danh mục: chữ HOA không dấu, số và gạch ngang. */
const CODE_PATTERN = /^[A-Z0-9-]+$/

export const documentPartnerSchema = z.object({
  // Bỏ trống thì backend tự sinh mã theo tiền tố `DVN`.
  code: z.union([
    z.literal(''),
    z
      .string()
      .trim()
      .max(30, 'Mã tối đa 30 ký tự')
      .regex(CODE_PATTERN, 'Chỉ dùng chữ HOA không dấu, số và dấu gạch ngang'),
  ]),
  name: z.string().trim().min(1, 'Nhập tên đơn vị').max(300, 'Tên tối đa 300 ký tự'),
  kind: z.union([
    z.literal(1),
    z.literal(2),
    z.literal(3),
    z.literal(4),
    z.literal(5),
  ]),
  contact_person: z.string().trim().max(200, 'Tối đa 200 ký tự'),
  phone: z.string().trim().max(50, 'Tối đa 50 ký tự'),
  email: z.union([z.literal(''), z.string().trim().email('Email không hợp lệ')]),
  address: z.string().trim().max(500, 'Tối đa 500 ký tự'),
  is_active: z.boolean(),
})

export type DocumentPartnerFormValues = z.infer<typeof documentPartnerSchema>
