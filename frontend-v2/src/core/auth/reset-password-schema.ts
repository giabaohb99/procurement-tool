import { z } from 'zod'

import { newPasswordField } from './password-rules'

/**
 * Schema form đặt lại mật khẩu (mở từ đường dẫn trong email khôi phục).
 *
 * Luật lấy đúng theo backend (`core/password_policy.py`, bao-CR-405) — để giao diện
 * báo trước thay vì bắt người dùng bấm gửi rồi mới nhận lỗi 400. Trước bao-CR-405
 * cửa `/api/auth/reset-password` **không kiểm gì cả**, ngưỡng 6 ký tự ghi ở đây chỉ
 * là chú thích sai chép từ cửa đổi mật khẩu.
 */
export const resetPasswordSchema = z
  .object({
    password: newPasswordField(),
    confirmPassword: z.string().min(1, 'Nhập lại mật khẩu mới'),
  })
  // Gắn lỗi vào Ô NHẬP LẠI chứ không vào cả form: người dùng thấy dòng đỏ ngay
  // dưới ô mình gõ sai, khỏi phải dò xem ô nào chưa khớp.
  .refine((values) => values.password === values.confirmPassword, {
    message: 'Mật khẩu nhập lại không khớp',
    path: ['confirmPassword'],
  })

export type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>
