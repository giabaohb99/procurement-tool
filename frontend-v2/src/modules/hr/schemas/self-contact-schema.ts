import { z } from 'zod'

import type { Employee } from '../types/employee'
import {
  cleanExtraPhones,
  extraPhonesFormError,
  extraPhonesSchema,
  type ExtraPhone,
} from './extra-phones-schema'

/**
 * Form TỰ SỬA LIÊN HỆ ở Trang cá nhân (bao-CR-508, khách chốt 28/09/2026).
 *
 * Số điện thoại (chính) + nhãn +  + số điện thoại khác (duoc-CR-694) + hai địa chỉ. Người báo tin đi cửa riêng
 * (`PUT /api/employees/me/contacts`) với bảng con của chính nó.
 *
 * ⚠️ `.max()` phải khớp ĐÚNG `SelfContactUpdate` ở
 * `backend/app/modules/employee/schema.py` (= `String(n)` ở `model.py`): rộng
 * hơn thì người dùng gõ hết ô rồi ăn câu 422 tiếng Anh, hẹp hơn thì chặn nhầm.
 */
export const selfContactSchema = z
  .object({
    phone: z.string().trim().max(25, 'Số điện thoại tối đa 25 ký tự'),
    phone_label: z.string().trim().max(50, 'Nhãn tối đa 50 ký tự'),
    extra_phones: extraPhonesSchema,
    permanent_address: z.string().trim().max(500, 'Địa chỉ thường trú tối đa 500 ký tự'),
    current_address: z.string().trim().max(500, 'Địa chỉ hiện nay tối đa 500 ký tự'),
  })
  .superRefine((values, ctx) => {
    const message = extraPhonesFormError(values.phone, values.extra_phones)
    if (message) ctx.addIssue({ code: 'custom', message, path: ['extra_phones'] })
  })

export type SelfContactFormValues = z.infer<typeof selfContactSchema>

/** Bốn ô đúng như backend nhận — không hơn một khóa nào. */
export type SelfContactPayload = SelfContactFormValues

/** Giá trị khởi tạo của form từ hồ sơ đang có — `null`/`undefined` thành chuỗi rỗng. */
export function toSelfContactFormValues(
  employee: Pick<Employee, 'phone' | 'phone_label' | 'permanent_address' | 'current_address'> & {
    extra_phones?: ExtraPhone[]
  },
): SelfContactFormValues {
  return {
    phone: employee.phone ?? '',
    phone_label: employee.phone_label ?? '',
    extra_phones: employee.extra_phones ?? [],
    permanent_address: employee.permanent_address ?? '',
    current_address: employee.current_address ?? '',
  }
}

/**
 * Dựng thân `PATCH /api/employees/me/contact` — NHẶT ĐÚNG bốn khóa, cắt khoảng trắng.
 *
 * ⚠️ Nhặt từng khóa chứ không `{ ...values }`: backend khai `extra="forbid"`
 * nên chỉ một khóa thừa (một ô ai đó thêm vào form "cho tiện", hay nguyên
 * object hồ sơ bị truyền nhầm vào) là cả lần lưu ăn 422. Nhặt ở đây thì form có
 * phình ra cũng không kéo khóa lạ theo.
 */
export function toSelfContactPayload(values: SelfContactFormValues): SelfContactPayload {
  return {
    phone: values.phone.trim(),
    phone_label: values.phone_label.trim(),
    extra_phones: cleanExtraPhones(values.extra_phones),
    permanent_address: values.permanent_address.trim(),
    current_address: values.current_address.trim(),
  }
}
