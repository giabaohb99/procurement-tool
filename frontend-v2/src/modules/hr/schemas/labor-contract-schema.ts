import { z } from 'zod'

import type { EmployeeDetail } from '../types/employee'
import type { LaborContract, LaborContractPayload } from '../types/labor-contract'
import { endDateRule } from '../utils/labor-contract-rules'

/** Trần tiền của backend (`Money`): số nguyên 0..10^12. */
export const MAX_MONEY = 10 ** 12

const money = (label: string) =>
  z
    .number({ invalid_type_error: `${label} phải là số` })
    .int(`${label} phải là số nguyên đồng`)
    .min(0, `${label} không được âm`)
    .max(MAX_MONEY, `${label} vượt mức cho phép`)

/**
 * Form hộp lập/sửa hợp đồng. Bám `LaborContractCreate` của backend (max_length
 * 50/100/255/500, tiền 0..10^12). Không `.default()` — giá trị đầu đặt ở `buildContractFormDefaults`.
 */
export const laborContractSchema = z
  .object({
    //  0 = chưa chọn.
    contract_type: z.number().int().min(1, 'Chọn loại hợp đồng'),
    contract_no: z.string().trim().max(50, 'Số HĐ tối đa 50 ký tự'),
    start_date: z.string().trim().min(1, 'Chọn ngày bắt đầu'),
    end_date: z.string().trim(),
    job_title: z.string().trim().max(100, 'Chức danh tối đa 100 ký tự'),
    work_location: z.string().trim().max(255, 'Địa điểm tối đa 255 ký tự'),
    base_salary: money('Lương cơ bản'),
    insurance_salary: money('Lương đóng BH'),
    allowance: money('Phụ cấp'),
    allowance_note: z.string().trim().max(500, 'Ghi chú phụ cấp tối đa 500 ký tự'),
    note: z.string().trim().max(500, 'Ghi chú tối đa 500 ký tự'),
  })
  .superRefine((v, ctx) => {
    if (v.end_date && v.start_date && v.end_date < v.start_date) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['end_date'],
        message: 'Ngày kết thúc phải sau hoặc bằng ngày bắt đầu',
      })
    }
    //  Loại chưa chọn (0) thì đã có lỗi ở ô loại — đừng chồng thêm lỗi ngày.
    if (v.contract_type < 1) return
    const rule = endDateRule(v.contract_type)
    if (rule === 'required' && !v.end_date) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['end_date'],
        message: 'Loại hợp đồng này bắt buộc có ngày kết thúc',
      })
    }
    if (rule === 'forbidden' && v.end_date) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['end_date'],
        message: 'Hợp đồng không xác định thời hạn thì không có ngày kết thúc',
      })
    }
  })

export type LaborContractFormValues = z.infer<typeof laborContractSchema>

/** Điền sẵn chức danh / nơi làm việc từ hồ sơ (backend cũng tự lấy khi để trống). */
export function buildContractFormDefaults(
  employee: Pick<EmployeeDetail, 'position' | 'work_location'>,
  row?: LaborContract | null,
): LaborContractFormValues {
  if (row) {
    return {
      contract_type: row.contract_type,
      contract_no: row.contract_no,
      start_date: row.start_date,
      end_date: row.end_date ?? '',
      job_title: row.job_title,
      work_location: row.work_location,
      base_salary: row.base_salary,
      insurance_salary: row.insurance_salary,
      allowance: row.allowance,
      allowance_note: row.allowance_note,
      note: row.note,
    }
  }
  return {
    contract_type: 0,
    contract_no: '',
    start_date: '',
    end_date: '',
    job_title: employee.position ?? '',
    work_location: employee.work_location ?? '',
    base_salary: 0,
    insurance_salary: 0,
    allowance: 0,
    allowance_note: '',
    note: '',
  }
}

/**
 * Giá trị form -> payload. Ngày kết thúc rỗng -> `null` (cột `DATE NULL`, KHÔNG gửi `""`
 * vì backend parse ngày sẽ 422). Chức danh / địa điểm rỗng: lúc LẬP -> `null` để backend lấy từ hồ sơ;
 * lúc SỬA -> `""` (backend bỏ qua `null` nên người dùng xóa trắng ô mà gửi `null` thì giá trị cũ ở lại).
 */
export function toLaborContractPayload(
  values: LaborContractFormValues,
  mode: 'create' | 'edit' = 'create',
): LaborContractPayload {
  const emptyText = mode === 'edit' ? '' : null
  return {
    contract_type: values.contract_type,
    contract_no: values.contract_no.trim(),
    start_date: values.start_date,
    end_date: values.end_date.trim() || null,
    job_title: values.job_title.trim() || emptyText,
    work_location: values.work_location.trim() || emptyText,
    base_salary: values.base_salary,
    insurance_salary: values.insurance_salary,
    allowance: values.allowance,
    allowance_note: values.allowance_note.trim(),
    note: values.note.trim(),
  }
}
