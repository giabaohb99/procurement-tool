import { z } from 'zod'

/**
 * Ràng buộc form VĂN BẢN — **bộ trường chung C01, cố định, khai trong mã**.
 *
 * Bản 1 không có trường nhập động và không nhập tệp mẫu Word. Văn bản mẫu trên
 * web chỉ cung cấp `content_html`; bộ trường chung vẫn cố định để tra cứu và
 * báo cáo được.
 *
 * KHÔNG có ô số hiệu — số do backend cấp trong cùng giao dịch ghi bản ghi, form
 * chỉ hiện dòng xem trước (D08). Ô `legacy_code` là chuyện khác: đó là số của
 * bản GIẤY trước khi lên hệ thống (C12), người dùng gõ tay.
 */
export const documentRecordSchema = z
  .object({
    doc_type_id: z.coerce.number().int().positive('Chọn loại văn bản'),
    company_id: z.coerce.number().int().positive('Chọn pháp nhân ban hành'),
    department_id: z.coerce.number().int().nullable(),
    //  Sổ văn bản: không bắt buộc. Vào sổ thì được cấp thêm số thứ tự trong sổ,
    //  và mọi thành viên của sổ đọc được văn bản này.
    book_id: z.coerce.number().int().nullable(),
    //  Người chịu trách nhiệm NỘI DUNG — người trả lời khi có ai hỏi về văn bản
    //  này. Bắt buộc: văn bản không có ai chịu trách nhiệm thì ba tháng sau
    //  không biết hỏi ai.
    owner_employee_id: z.coerce.number().int().positive('Chọn người chịu trách nhiệm nội dung'),
    drafter_employee_id: z.coerce.number().int().nullable(),
    signer_employee_id: z.coerce.number().int().nullable(),

    title: z.string().trim().min(1, 'Nhập tên văn bản').max(500, 'Tối đa 500 ký tự'),
    summary: z.string().trim().max(2000, 'Tối đa 2000 ký tự'),
    keywords: z.string().trim().max(500, 'Tối đa 500 ký tự'),

    secrecy_level: z.coerce.number().int().min(1).max(4),
    urgency: z.coerce.number().int().min(1).max(3),

    effective_date: z.string(),
    expire_date: z.string(),
    legacy_code: z.string().trim().max(100, 'Tối đa 100 ký tự'),
  })
  // Khoảng hiệu lực ngược đầu là lỗi nhập liệu, không phải trường hợp hợp lệ.
  .refine(
    (values) =>
      !values.effective_date || !values.expire_date || values.effective_date <= values.expire_date,
    { path: ['expire_date'], message: 'Ngày hết hiệu lực phải sau ngày bắt đầu' },
  )

export type DocumentRecordFormValues = z.infer<typeof documentRecordSchema>
