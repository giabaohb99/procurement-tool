import { z } from 'zod'

/**
 * Schema form đặt lại mật khẩu (mở từ đường dẫn trong email khôi phục).
 *
 * Ngưỡng 6 ký tự lấy đúng theo backend (`/api/auth/reset-password` và
 * `/api/auth/change-password` đều chặn ở 6) — để giao diện báo trước thay vì
 * bắt người dùng bấm gửi rồi mới nhận lỗi 400.
 */
export const resetPasswordSchema = z
  .object({
    password: z.string().min(6, 'Mật khẩu mới phải từ 6 ký tự trở lên'),
    confirmPassword: z.string().min(1, 'Nhập lại mật khẩu mới'),
  })
  // Gắn lỗi vào Ô NHẬP LẠI chứ không vào cả form: người dùng thấy dòng đỏ ngay
  // dưới ô mình gõ sai, khỏi phải dò xem ô nào chưa khớp.
  .refine((values) => values.password === values.confirmPassword, {
    message: 'Mật khẩu nhập lại không khớp',
    path: ['confirmPassword'],
  })

export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>
