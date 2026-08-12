import { z } from 'zod'

/** Schema form đăng nhập — nguồn sự thật cho cả validate lẫn kiểu TS của form. */
export const loginSchema = z.object({
  username: z.string().trim().min(1, 'Nhập mã nhân viên hoặc email'),
  password: z.string().min(1, 'Nhập mật khẩu'),
})

export type LoginFormValues = z.infer<typeof loginSchema>
