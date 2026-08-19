import { z } from 'zod'

/**
 * Schema form đổi mật khẩu ở Trang cá nhân.
 *
 * Ba luật dưới đây lặp lại đúng ba lần backend từ chối
 * (`POST /api/auth/change-password`): thiếu mật khẩu hiện tại, mật khẩu mới
 * ngắn hơn 6 ký tự, mật khẩu mới trùng mật khẩu cũ. Kiểm trước ở giao diện để
 * người dùng không phải gửi lên mới biết mình gõ hụt.
 */
export const changePasswordSchema = z
  .object({
    oldPassword: z.string().min(1, 'Nhập mật khẩu hiện tại'),
    newPassword: z.string().min(6, 'Mật khẩu mới phải từ 6 ký tự trở lên'),
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
