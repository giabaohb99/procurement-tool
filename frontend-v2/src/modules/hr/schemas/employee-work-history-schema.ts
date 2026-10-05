import { z } from 'zod'

/**
 * Form hộp thêm/sửa «Quá trình công tác». Bám sát `WorkHistoryIn` của backend
 * (phase 02) để không dính 422.
 *
 * ⚠️ Cùng quy ước với `employee-schema.ts`: KHÔNG `.default()` / `.coerce` —
 * giá trị khởi tạo đặt ở `EMPTY_EMPLOYEE_WORK_HISTORY_FORM`.
 */
export const employeeWorkHistorySchema = z
  .object({
    //  Mã số của `WorkEventType` — `0` = chưa chọn, không nằm trong bộ mã nên
    //  Select không khớp mục nào và hiện đúng placeholder "Chọn loại".
    event_type: z.number().int().min(1, 'Chọn loại'),
    //  Ngày HIỆU LỰC (Q1) — bắt buộc.
    from_date: z.string().trim().min(1, 'Chọn từ ngày'),
    //  Để trống = đang hiệu lực.
    to_date: z.string().trim(),
    //  0 = chưa chọn (sentinel, cùng quy ước với `employee-schema.ts`).
    company_id: z.number().int().min(0),
    department_id: z.number().int().min(0),
    position_id: z.number().int().min(0),
    decision_no: z.string().trim().max(50, 'Số QĐ tối đa 50 ký tự'),
    decision_date: z.string().trim(),
    note: z.string().trim().max(500, 'Ghi chú tối đa 500 ký tự'),
    //  Tick «Đóng dòng đang hiệu lực… vào ngày trước đó» — chỉ hiện ô này khi
    //  đang tạo dòng NHÓM CHÍNH và có dòng chính khác còn mở (xem form dialog).
    close_open_main: z.boolean(),
  })
  .refine((v) => !v.to_date || v.to_date >= v.from_date, {
    path: ['to_date'],
    message: 'Đến ngày phải sau hoặc bằng từ ngày',
  })

export type EmployeeWorkHistoryFormValues = z.infer<typeof employeeWorkHistorySchema>

/**
 * Biến thể khi hộp mở từ tab «Quyết định bổ nhiệm» (nút «+ Thêm quyết định»,
 * 03/10/2026) — cùng hộp, cùng ô, chỉ khác Số QĐ chuyển từ tùy chọn sang BẮT
 * BUỘC. Ở tab «Quá trình công tác», Số QĐ vẫn tùy chọn (không phải dòng nào
 * cũng có quyết định bằng văn bản).
 */
export const employeeWorkHistoryDecisionSchema = employeeWorkHistorySchema.refine(
  (v) => v.decision_no.trim() !== '',
  { path: ['decision_no'], message: 'Nhập số QĐ' },
)

export const EMPTY_EMPLOYEE_WORK_HISTORY_FORM: EmployeeWorkHistoryFormValues = {
  event_type: 0,
  from_date: '',
  to_date: '',
  company_id: 0,
  department_id: 0,
  position_id: 0,
  decision_no: '',
  decision_date: '',
  note: '',
  close_open_main: true,
}
