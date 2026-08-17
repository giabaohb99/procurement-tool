import { z } from 'zod'

/**
 * Ràng buộc form Quy tắc đánh số.
 *
 * Ba luật ở dưới trước đây nằm rải trong hàm `submit()` của hộp thoại và chỉ
 * báo được MỘT lỗi mỗi lần bấm. Đưa về schema thì lỗi hiện ngay dưới đúng ô sai
 * và hiện hết cùng lúc — giống mọi form khác của phân hệ.
 */

/** Không có `{STT}` thì mẫu số không có chỗ để đặt số thứ tự → mọi văn bản trùng số. */
const SEQ_TOKEN = '{STT}'

export const documentNumberingRuleSchema = z
  .object({
    direction: z.union([z.literal(1), z.literal(2), z.literal(3)]),
    pattern: z
      .string()
      .trim()
      .min(1, 'Nhập mẫu số hiệu')
      .max(200, 'Mẫu số tối đa 200 ký tự')
      .refine((value) => value.includes(SEQ_TOKEN), `Mẫu số phải có ${SEQ_TOKEN}`),

    start_no: z.coerce
      .number()
      .int('Nhập số nguyên')
      .min(1, 'Số bắt đầu từ 1 trở lên')
      .max(999999, 'Số quá lớn'),
    priority: z.coerce
      .number()
      .int('Nhập số nguyên')
      .min(1, 'Mức ưu tiên từ 1 trở lên')
      .max(9999, 'Mức ưu tiên tối đa 9999'),

    reset_yearly: z.boolean(),
    allow_manual: z.boolean(),
    is_active: z.boolean(),

    /** 1 tất cả loại · 2 chọn loại. */
    doc_type_mode: z.union([z.literal(1), z.literal(2)]),
    /** 1 tất cả sổ · 2 chọn sổ · 3 văn bản không vào sổ. */
    book_mode: z.union([z.literal(1), z.literal(2), z.literal(3)]),
    doc_type_ids: z.array(z.number()),
    book_ids: z.array(z.number()),
  })
  //  Chọn "chọn loại"/"chọn sổ" mà bỏ trống danh sách thì quy tắc không bao giờ
  //  khớp văn bản nào — lưu được nhưng vô dụng, nên chặn ngay tại form.
  .superRefine((values, ctx) => {
    if (values.doc_type_mode === 2 && values.doc_type_ids.length === 0) {
      ctx.addIssue({
        code: 'custom',
        path: ['doc_type_ids'],
        message: 'Chọn ít nhất một loại văn bản',
      })
    }
    if (values.book_mode === 2 && values.book_ids.length === 0) {
      ctx.addIssue({
        code: 'custom',
        path: ['book_ids'],
        message: 'Chọn ít nhất một sổ văn bản',
      })
    }
  })

export type DocumentNumberingRuleFormValues = z.infer<typeof documentNumberingRuleSchema>
