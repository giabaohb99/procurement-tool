import { z } from 'zod'

/**
 * Luật mật khẩu phía giao diện — chép đúng `backend/app/core/password_policy.py`
 * (bao-CR-405 / BM-016) để người dùng biết mình gõ hụt TRƯỚC khi bấm gửi.
 *
 * Chỉ chép được các luật không cần ngữ cảnh. Luật mạnh nhất của backend —
 * **mật khẩu không được chứa mã nhân viên hoặc email của tài khoản** — cần dữ liệu
 * mà form không có, nên nó chỉ nổ ở máy chủ và trả về câu 400 đọc được.
 * Ở đây CỐ Ý không đoán lại: thà để một mật khẩu lọt qua ô nhập rồi bị máy chủ từ
 * chối, còn hơn dựng một luật gần đúng rồi chặn nhầm mật khẩu hợp lệ.
 */
export const PASSWORD_MIN_LENGTH = 8

/** bcrypt băm tối đa 72 byte và cắt âm thầm phần dư — backend chặn thẳng ở mốc này. */
export const PASSWORD_MAX_BYTES = 72

export const PASSWORD_HINT = `Tối thiểu ${PASSWORD_MIN_LENGTH} ký tự, phải có cả chữ và số.`

const byteLength = (value: string) => new TextEncoder().encode(value).length

/** Ô nhập mật khẩu MỚI. Dùng chung cho form đổi mật khẩu và form đặt lại mật khẩu. */
export const newPasswordField = () =>
  z
    .string()
    .min(PASSWORD_MIN_LENGTH, `Mật khẩu mới phải từ ${PASSWORD_MIN_LENGTH} ký tự trở lên`)
    .refine((value) => value === value.trim(), {
      message: 'Mật khẩu không được bắt đầu hoặc kết thúc bằng khoảng trắng',
    })
    .refine((value) => byteLength(value) <= PASSWORD_MAX_BYTES, {
      message: `Mật khẩu quá dài — tối đa ${PASSWORD_MAX_BYTES} byte`,
    })
    .refine((value) => /[a-zA-Z]/.test(value) && /\d/.test(value), {
      message: 'Mật khẩu phải có cả chữ và số',
    })
