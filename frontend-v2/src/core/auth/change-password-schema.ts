import { z } from 'zod'

import { newPasswordField } from './password-rules'

/**
 * Schema form đổi mật khẩu ở Trang cá nhân.
 *
 * Các luật dưới đây lặp lại đúng những lần backend từ chối
 * (`POST /api/auth/change-password`): thiếu mật khẩu hiện tại, mật khẩu mới không
 * đạt chính sách (`password-rules`, bao-CR-405), mật khẩu mới trùng mật khẩu cũ.
 * Kiểm trước ở giao diện để người dùng không phải gửi lên mới biết mình gõ hụt.
 */
export const changePasswordSchema = z
  .object({
    oldPassword: z.string().min(1, 'Nhập mật khẩu hiện tại'),
    newPassword: newPasswordField(),
    confirmPassword: z.string().min(1, 'Nhập lại mật khẩu mới'),
  })
  .refine((values) => values.newPassword === values.confirmPassword, {
    message: 'Mật khẩu nhập lại không khớp',
    path: ['confirmPassword'],
  })
  .refine((values) => values.newPassword !== values.oldPassword, {
    message: 'Mật khẩu mới không được trùng mật khẩu cũ',
    path: ['newPassword'],
  })

export type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>
