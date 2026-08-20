import { z } from 'zod'

/**
 * Kiểu dữ liệu ghi của nhà cung cấp, dùng cho `supplier-api.ts`.
 *
 * ⚠️ Màn Nhà cung cấp KHÔNG còn chạy qua schema này: từ khi dời sang khung
 * Generic CRUD (`config/supplier-crud.tsx`), form do `CrudFormDialog` dựng và
 * ràng buộc khai ngay trong `formFields`. Sửa luật nhập liệu ở đây KHÔNG đổi gì
 * trên màn — sửa trong config. Giữ file lại vì tầng API vẫn lấy kiểu từ đây, và
 * vì đây là mẫu quy ước schema form được các phân hệ khác dẫn chiếu.
 *
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
  // Lưu dạng thập phân (0.08 = 8%). Người dùng nhập theo phần trăm, quy đổi ở
  // `shared/crud/field-values.ts` (trường khai `type: 'percent'`).
  vat: z.number().min(0, 'VAT không âm').max(1, 'VAT tối đa 100%'),
  is_active: z.boolean(),
})

export type SupplierFormValues = z.infer<typeof supplierSchema>
