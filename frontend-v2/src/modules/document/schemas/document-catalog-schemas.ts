import { z } from 'zod'

import {
  SECURITY_LEVEL_KIND_CONFIDENTIAL,
  SECURITY_LEVEL_KIND_URGENCY,
} from '../types/security-level'

/**
 * Ràng buộc form của hai danh mục ĐƠN VỊ GỬI NHẬN và MỨC MẬT / ĐỘ KHẨN.
 *
 * Trường động (danh mục thứ ba trước đây định ở tệp này) đã bỏ khỏi bản 1 vì
 * soạn thảo gõ thẳng trên web.
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

/**
 * Mã bậc mức mật / độ khẩn: chữ HOA không dấu, số và GẠCH DƯỚI — khác gạch
 * ngang của `documentPartnerSchema`, khớp `CODE_PATTERN` ở
 * `backend/app/modules/doc_catalog/security_level_schema.py`.
 */
const SECURITY_LEVEL_CODE_PATTERN = /^[A-Z0-9_]+$/

/**
 * Ràng buộc form một bậc mức mật / độ khẩn.
 *
 * `kind` và `value` CÓ trong schema (cần cho lúc TẠO MỚI) nhưng form ở chế độ
 * SỬA khóa hai ô đó và KHÔNG gửi chúng lên PATCH — xem
 * `pages/security-level-detail-page.tsx` và lý do ở đầu `types/security-level.ts`.
 */
export const securityLevelSchema = z.object({
  kind: z.union([
    z.literal(SECURITY_LEVEL_KIND_CONFIDENTIAL),
    z.literal(SECURITY_LEVEL_KIND_URGENCY),
  ]),
  // Dải rộng như backend (`VALUE_MAX = 99`) — không phải giới hạn nghiệp vụ mà
  // chỉ chặn gõ nhầm.
  value: z.coerce.number().int('Nhập số nguyên').min(1, 'Tối thiểu 1').max(99, 'Tối đa 99'),
  code: z
    .string()
    .trim()
    .min(1, 'Nhập mã bậc')
    .max(30, 'Mã tối đa 30 ký tự')
    .regex(SECURITY_LEVEL_CODE_PATTERN, 'Chỉ dùng chữ HOA không dấu, số và dấu gạch dưới'),
  name: z.string().trim().min(1, 'Nhập tên bậc').max(100, 'Tên tối đa 100 ký tự'),
  description: z.string().trim().max(500, 'Mô tả tối đa 500 ký tự'),
  is_active: z.boolean(),
})

export type SecurityLevelFormValues = z.infer<typeof securityLevelSchema>
