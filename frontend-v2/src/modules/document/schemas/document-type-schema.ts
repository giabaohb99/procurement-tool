import { z } from 'zod'

/**
 * Ràng buộc form Loại văn bản.
 *
 * `code` và `prefix` chỉ cho chữ HOA không dấu, số và gạch ngang: hai giá trị
 * này đi vào số hiệu văn bản (`CV-2026-001`) nên có dấu tiếng Việt hay khoảng
 * trắng là hỏng cả chuỗi mã.
 */
const CODE_PATTERN = /^[A-Z0-9-]+$/

export const documentTypeSchema = z.object({
  code: z
    .string()
    .trim()
    .min(1, 'Nhập mã loại')
    .max(20, 'Mã tối đa 20 ký tự')
    .regex(CODE_PATTERN, 'Chỉ dùng chữ HOA không dấu, số và dấu gạch ngang'),
  name: z.string().trim().min(1, 'Nhập tên loại văn bản').max(120, 'Tên tối đa 120 ký tự'),
  prefix: z
    .string()
    .trim()
    .min(1, 'Nhập tiền tố số hiệu')
    .max(10, 'Tiền tố tối đa 10 ký tự')
    .regex(CODE_PATTERN, 'Chỉ dùng chữ HOA không dấu, số và dấu gạch ngang'),
  description: z.string().trim().max(255, 'Mô tả tối đa 255 ký tự'),
  is_active: z.boolean(),

  // Tùy chọn khác — xem `DOCUMENT_TYPE_OPTIONS` để biết từng cái nghĩa gì.
  has_template: z.boolean(),
  has_version: z.boolean(),
  needs_approval: z.boolean(),
  needs_issue_decision: z.boolean(),
  needs_signature: z.boolean(),
  is_confidential: z.boolean(),
})

export type DocumentTypeFormValues = z.infer<typeof documentTypeSchema>
