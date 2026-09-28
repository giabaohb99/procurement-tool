import { z } from 'zod'

import type { Employee } from '../types/employee'

/**
 * Form TỰ SỬA LIÊN HỆ ở Trang cá nhân (bao-CR-508, khách chốt 28/09/2026).
 *
 * Chỉ ba ô: số điện thoại + hai địa chỉ. Người báo tin đi cửa riêng
 * (`PUT /api/employees/me/contacts`) với bảng con của chính nó.
 *
 * ⚠️ `.max()` phải khớp ĐÚNG `SelfContactUpdate` ở
 * `backend/app/modules/employee/schema.py` (= `String(n)` ở `model.py`): rộng
 * hơn thì người dùng gõ hết ô rồi ăn câu 422 tiếng Anh, hẹp hơn thì chặn nhầm.
 */
export const selfContactSchema = z.object({
  phone: z.string().trim().max(25, 'Số điện thoại tối đa 25 ký tự'),
  permanent_address: z.string().trim().max(500, 'Địa chỉ thường trú tối đa 500 ký tự'),
  current_address: z.string().trim().max(500, 'Địa chỉ hiện nay tối đa 500 ký tự'),
})

export type SelfContactFormValues = z.infer<typeof selfContactSchema>

/** Ba ô đúng như backend nhận — không hơn một khóa nào. */
export type SelfContactPayload = SelfContactFormValues

/** Giá trị khởi tạo của form từ hồ sơ đang có — `null`/`undefined` thành chuỗi rỗng. */
export function toSelfContactFormValues(
  employee: Pick<Employee, 'phone' | 'permanent_address' | 'current_address'>,
): SelfContactFormValues {
  return {
    phone: employee.phone ?? '',
    permanent_address: employee.permanent_address ?? '',
    current_address: employee.current_address ?? '',
  }
}

/**
 * Dựng thân `PATCH /api/employees/me/contact` — NHẶT ĐÚNG ba khóa, cắt khoảng trắng.
 *
 * ⚠️ Nhặt từng khóa chứ không `{ ...values }`: backend khai `extra="forbid"`
 * nên chỉ một khóa thừa (một ô ai đó thêm vào form "cho tiện", hay nguyên
 * object hồ sơ bị truyền nhầm vào) là cả lần lưu ăn 422. Nhặt ở đây thì form có
 * phình ra cũng không kéo khóa lạ theo.
 */
export function toSelfContactPayload(values: SelfContactFormValues): SelfContactPayload {
  return {
    phone: values.phone.trim(),
    permanent_address: values.permanent_address.trim(),
    current_address: values.current_address.trim(),
  }
}
