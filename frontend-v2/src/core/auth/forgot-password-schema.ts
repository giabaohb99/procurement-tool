import { z } from 'zod'

/** Schema form khôi phục mật khẩu. */
export const forgotPasswordSchema = z.object({
  email: z.string().trim().min(1, 'Nhập địa chỉ email').email('Email không hợp lệ'),
})

export type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>
