import { z } from 'zod'

/**
 * Ràng buộc form VĂN BẢN.
 *
 * `code` (số văn bản) được nhập tay nhưng KHÔNG bắt buộc: bỏ trống thì hệ ghép
 * số lúc lưu (`helpers/document-number.ts`). Số vào sổ vẫn do hệ cấp, người
 * dùng không đụng tới.
 */
export const documentRecordSchema = z
  .object({
    code: z.string().trim().max(50, 'Tối đa 50 ký tự'),
    direction: z.enum(['incoming', 'outgoing', 'internal']),
    document_type_id: z.coerce.number().int().positive('Chọn loại văn bản'),
    doc_format: z.enum(['original', 'certified_copy', 'electronic', 'fax']),
    confidential_level_id: z.coerce.number().int().nullable(),
    urgent_level_id: z.coerce.number().int().nullable(),
    partner_id: z.coerce.number().int().nullable(),
    recipients: z.array(z.string().trim().min(1)).max(50, 'Tối đa 50 nơi nhận'),
    is_important: z.boolean(),
    is_urgent: z.boolean(),

    title: z.string().trim().min(1, 'Nhập tên văn bản').max(255, 'Tối đa 255 ký tự'),
    summary: z.string().trim().max(2000, 'Tối đa 2000 ký tự'),
    signer: z.string().trim().max(120, 'Tối đa 120 ký tự'),
    approver: z.string().trim().max(120, 'Tối đa 120 ký tự'),
    drafting_department: z.string().trim().max(120, 'Tối đa 120 ký tự'),

    issued_date: z.string().min(1, 'Chọn ngày ban hành'),
    sent_date: z.string(),
    received_date: z.string(),
    required_due_date: z.string(),
    effective_from: z.string(),
    effective_to: z.string(),
    status: z.enum(['draft', 'effective', 'replaced', 'revoked']),

    processing_status: z.enum(['pending', 'processing', 'done', 'on_hold']),
    handler: z.string().trim().max(120, 'Tối đa 120 ký tự'),
    related_person: z.string().trim().max(120, 'Tối đa 120 ký tự'),
    report_receiver: z.string().trim().max(120, 'Tối đa 120 ký tự'),
    due_date: z.string(),
    result: z.string().trim().max(500, 'Tối đa 500 ký tự'),
    processing_note: z.string().trim().max(1000, 'Tối đa 1000 ký tự'),
    storage_location: z.string().trim().max(120, 'Tối đa 120 ký tự'),
  })
  // Nơi gửi / nơi nhận (`partner_id`) và ngày đến KHÔNG còn bắt buộc: form tạo
  // mới hỏi nơi nhận bằng danh sách tên (`recipients`), còn hai ô kia chỉ hiện
  // ở trang chi tiết. Bắt buộc ở đây là chặn luôn nút "Tạo".
  // Khoảng hiệu lực ngược đầu là lỗi nhập liệu, không phải trường hợp hợp lệ.
  .refine(
    (values) =>
      !values.effective_from ||
      !values.effective_to ||
      values.effective_from <= values.effective_to,
    { path: ['effective_to'], message: 'Ngày hết hiệu lực phải sau ngày bắt đầu' },
  )
  // Giao việc thì phải có người nhận, nếu không "Đang xử lý" là xử lý bởi ai?
  .refine(
    (values) => values.processing_status !== 'processing' || Boolean(values.handler),
    { path: ['handler'], message: 'Chọn người xử lý khi đã chuyển sang Đang xử lý' },
  )

export type DocumentRecordFormValues = z.infer<typeof documentRecordSchema>
