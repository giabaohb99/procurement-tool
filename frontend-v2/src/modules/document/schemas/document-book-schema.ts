import { z } from 'zod'

/**
 * Ràng buộc form Sổ văn bản.
 *
 * `code` chỉ nhập được lúc tạo mới và **không sửa được về sau**: mã sổ là khóa
 * của bộ đếm (`book:{mã}:{năm}`), đổi mã là bộ đếm cũ mồ côi và sổ đếm lại từ 1
 * trong khi số cũ đã phát ra ngoài.
 */
const CODE_PATTERN = /^[A-Z0-9-]+$/

export const documentBookSchema = z.object({
  // Bỏ trống thì backend tự sinh theo loại sổ (SD/SDI/SNB + số thứ tự).
  code: z.union([
    z.literal(''),
    z
      .string()
      .trim()
      .max(30, 'Mã tối đa 30 ký tự')
      .regex(CODE_PATTERN, 'Chỉ dùng chữ HOA không dấu, số và dấu gạch ngang'),
  ]),
  name: z.string().trim().min(1, 'Nhập tên sổ').max(200, 'Tên tối đa 200 ký tự'),
  kind: z.union([z.literal(1), z.literal(2), z.literal(3)]),
  description: z.string().trim().max(1000, 'Mô tả tối đa 1000 ký tự'),

  company_id: z.coerce.number().int().min(1, 'Chọn pháp nhân sở hữu sổ'),

  number_prefix: z.string().trim().max(20, 'Tiền tố tối đa 20 ký tự'),
  reset_yearly: z.boolean(),
  start_no: z.coerce
    .number()
    .int('Nhập số nguyên')
    .min(1, 'Số bắt đầu từ 1 trở lên')
    .max(999999, 'Số quá lớn'),

  // Người quản lý là người duy nhất sửa và xóa được sổ — không cử ai thì lúc
  // cần đóng sổ hay sửa tiền tố không ai có thẩm quyền làm.
  manager_ids: z.array(z.number()).min(1, 'Chọn ít nhất một người quản lý'),
  viewer_ids: z.array(z.number()),
  is_active: z.boolean(),
})

export type DocumentBookFormValues = z.infer<typeof documentBookSchema>
