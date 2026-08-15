import { z } from 'zod'

const ISSUE_CODE_PATTERN = /^[A-Z0-9]*$/

/** Form công ty (pháp nhân) — bám `CompanyCreate` của backend. */
export const companySchema = z.object({
  // Bỏ trống khi tạo mới thì backend tự sinh mã dạng CTY0001.
  code: z.string().trim().max(50, 'Mã tối đa 50 ký tự'),
  name: z.string().trim().min(1, 'Nhập tên pháp nhân').max(255, 'Tên tối đa 255 ký tự'),
  issue_code: z
    .string()
    .trim()
    .max(20, 'Mã số hiệu tối đa 20 ký tự')
    .regex(ISSUE_CODE_PATTERN, 'Chỉ dùng chữ HOA không dấu và số'),
  short_name: z.string().trim().max(100, 'Tên viết tắt tối đa 100 ký tự'),
  level: z.number().int().min(1).max(3),
  tax_code: z.string().trim().max(25, 'Mã số thuế tối đa 25 ký tự'),
  address: z.string().trim(),
  invoice_email: z.string().trim().max(150, 'Email tối đa 150 ký tự'),
  /** ID pháp nhân cấp trên; 0 = công ty gốc. */
  parent: z.number().int().min(0),
  /** Nhân sự ký thay mặt pháp nhân. `null` = chưa chỉ định. */
  legal_representative_id: z.number().int().nullable(),
  /** Chức danh in trên hợp đồng / chứng từ, vd "Giám đốc". */
  legal_rep_title: z.string().trim().max(100, 'Chức danh tối đa 100 ký tự'),
  is_active: z.boolean(),
})

export type CompanyFormValues = z.infer<typeof companySchema>

export const EMPTY_COMPANY_FORM: CompanyFormValues = {
  code: '',
  name: '',
  issue_code: '',
  short_name: '',
  level: 2,
  tax_code: '',
  address: '',
  invoice_email: '',
  parent: 0,
  legal_representative_id: null,
  legal_rep_title: '',
  is_active: true,
}
