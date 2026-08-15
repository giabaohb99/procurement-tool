import { z } from 'zod'

export const documentTemplateSchema = z.object({
  doc_type_id: z.coerce.number().int().positive('Chọn loại văn bản'),
  name: z.string().trim().min(1, 'Nhập tên văn bản mẫu').max(200, 'Tối đa 200 ký tự'),
  description: z.string().trim().max(2000, 'Tối đa 2000 ký tự'),
  content_html: z.string(),
  is_active: z.boolean(),
})

export type DocumentTemplateFormValues = z.infer<typeof documentTemplateSchema>
