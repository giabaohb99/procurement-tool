import { z } from 'zod'

import { CONCURRENT_KIND_COMPANY, CONCURRENT_KIND_DEPARTMENT } from '../types/employee-concurrent'

/** Dải ngày khớp `ConcurrentDate` của backend (1900-2100) — gõ nhầm năm 2206 thì báo ngay ở ô, không đợi 422. */
const MIN_DATE = '1900-01-01'
const MAX_DATE = '2100-12-31'
const RANGE_MESSAGE = 'Ngày phải trong khoảng 01/01/1900 - 31/12/2100'

function inRange(value: string): boolean {
  return !value || (value >= MIN_DATE && value <= MAX_DATE)
}

/**
 * Form hộp thêm/sửa KIÊM NHIỆM — bám `ConcurrentIn` (`concurrent_schema.py`, duoc-CR-756): chọn **Loại** trước; loại
 * Phòng ban bắt buộc phòng (`> 0`), loại Công ty bắt buộc công ty (`> 0`); từ ngày bắt buộc, Số QĐ ≤ 50, Ghi chú ≤ 500,
 * đến ngày ≥ từ ngày. Form giữ cả hai ô `company_id` / `department_id` nhưng chỉ ô của loại đang chọn được kiểm và được
 * gửi đi (`toConcurrentCreatePayload`). Cùng quy ước `employee-work-history-schema.ts`: KHÔNG `.default()` / `.coerce`,
 * giá trị khởi tạo ở `EMPTY_EMPLOYEE_CONCURRENT_FORM`.
 */
export const employeeConcurrentSchema = z
  .object({
    kind: z.number().int().refine((v) => v === CONCURRENT_KIND_DEPARTMENT || v === CONCURRENT_KIND_COMPANY, 'Chọn loại'),
    company_id: z.number().int().min(0),
    department_id: z.number().int().min(0),
    position_id: z.number().int().min(0),
    from_date: z.string().trim().min(1, 'Chọn từ ngày').refine(inRange, RANGE_MESSAGE),
    to_date: z.string().trim().refine(inRange, RANGE_MESSAGE),
    decision_no: z.string().trim().max(50, 'Số QĐ tối đa 50 ký tự'),
    decision_date: z.string().trim().refine(inRange, RANGE_MESSAGE),
    note: z.string().trim().max(500, 'Ghi chú tối đa 500 ký tự'),
    counts_scope: z.boolean(),
  })
  .superRefine((v, ctx) => {
    if (v.kind === CONCURRENT_KIND_DEPARTMENT && v.department_id <= 0) {
      ctx.addIssue({ code: 'custom', path: ['department_id'], message: 'Chọn phòng ban' })
    }
    if (v.kind === CONCURRENT_KIND_COMPANY && v.company_id <= 0) {
      ctx.addIssue({ code: 'custom', path: ['company_id'], message: 'Chọn công ty' })
    }
    if (v.to_date && v.from_date && v.to_date < v.from_date) {
      ctx.addIssue({ code: 'custom', path: ['to_date'], message: 'Đến ngày phải sau hoặc bằng từ ngày' })
    }
  })

export type EmployeeConcurrentFormValues = z.infer<typeof employeeConcurrentSchema>

/** Dòng mới mặc định loại Phòng ban, BẬT công tắc phạm vi — khớp mặc định `counts_scope=True` của backend. */
export const EMPTY_EMPLOYEE_CONCURRENT_FORM: EmployeeConcurrentFormValues = {
  kind: CONCURRENT_KIND_DEPARTMENT,
  company_id: 0,
  department_id: 0,
  position_id: 0,
  from_date: '',
  to_date: '',
  decision_no: '',
  decision_date: '',
  note: '',
  counts_scope: true,
}
