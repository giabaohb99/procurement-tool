import { z } from 'zod'

/**
 * Nguồn sự thật DUY NHẤT cho form nhà cung cấp: vừa validate, vừa sinh kiểu TS.
 * Ràng buộc phải bám sát backend (`SupplierCreate`) để không bị 422 sau khi submit.
 *
 * ⚠️ QUY ƯỚC CHO MỌI SCHEMA FORM: KHÔNG dùng `.default()` và `.coerce`.
 * Hai thứ đó làm kiểu ĐẦU VÀO khác kiểu ĐẦU RA của schema, còn react-hook-form
 * lại suy ra một kiểu duy nhất -> lỗi biên dịch rất khó đọc ở `useForm`.
 * Giá trị khởi tạo đặt ở `defaultValues` của form, ép kiểu làm trong `onChange`.
 */
export const supplierSchema = z.object({
  code: z
    .string()
    .trim()
    .min(1, 'Nhập tên viết tắt')
    .max(50, 'Tên viết tắt tối đa 50 ký tự'),
  name: z.string().trim().min(1, 'Nhập tên nhà cung cấp').max(255, 'Tên tối đa 255 ký tự'),
  supplier_type: z.enum(['goods', 'transport']),
  tax_code: z.string().trim().max(25, 'Mã số thuế tối đa 25 ký tự'),
  phone: z.string().trim().max(30, 'Số điện thoại tối đa 30 ký tự'),
  contact_person: z.string().trim().max(100, 'Người liên hệ tối đa 100 ký tự'),
  address: z.string().trim(),
  // Lưu dạng thập phân (0.08 = 8%). Người dùng nhập theo phần trăm, quy đổi ở form —
  // xem `supplier-form-dialog.tsx`.
  vat: z.number().min(0, 'VAT không âm').max(1, 'VAT tối đa 100%'),
  is_active: z.boolean(),
})

export type SupplierFormValues = z.infer<typeof supplierSchema>
