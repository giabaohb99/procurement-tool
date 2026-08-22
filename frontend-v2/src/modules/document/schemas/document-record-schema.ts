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
    //  Bắt buộc: bước đầu luồng duyệt là «trưởng bộ phận của phòng chủ trì»,
    //  bỏ trống thì gửi duyệt xong phiên chốt ở trạng thái KẸT và văn bản không
    //  đi tiếp được bằng đường nào.
    department_id: z.coerce.number().int().positive('Chọn phòng chủ trì'),
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

    // Mức mật / độ khẩn nay là danh mục sửa được (`tab_security_level`), dải
    // hợp lệ thật do backend kiểm theo danh mục — hai chặn dưới đây chỉ khớp
    // biên `VALUE_MAX` của backend (bắt gõ nhầm, không phải luật nghiệp vụ).
    secrecy_level: z.coerce.number().int().min(1).max(99),
    urgency: z.coerce.number().int().min(1).max(99),

    effective_date: z.string(),
    expire_date: z.string(),
    legacy_code: z.string().trim().max(100, 'Tối đa 100 ký tự'),
    //  NƠI LƯU TRỮ CỨNG — bản giấy có chữ ký tươi nằm ở đâu. Không bắt buộc:
    //  lúc lập văn bản thì thường chưa in ra, chỗ cất là chuyện sau khi ký.
    storage_location: z.string().trim().max(200, 'Tối đa 200 ký tự'),
  })
  // Khoảng hiệu lực ngược đầu là lỗi nhập liệu, không phải trường hợp hợp lệ.
  .refine(
    (values) =>
      !values.effective_date || !values.expire_date || values.effective_date <= values.expire_date,
    { path: ['expire_date'], message: 'Ngày hết hiệu lực phải sau ngày bắt đầu' },
  )

export type DocumentRecordFormValues = z.infer<typeof documentRecordSchema>
