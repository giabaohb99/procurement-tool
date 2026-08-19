import { describe, expect, it } from 'vitest'

import { resetPasswordSchema } from './reset-password-schema'

/**
 * Màn đặt lại mật khẩu là màn CÔNG KHAI — ai cầm được đường dẫn cũng mở được.
 * Bốn khẳng định dưới đây giữ đúng phần kiểm tra tại chỗ, để lỗi hiện ngay dưới
 * ô nhập thay vì phải gọi API rồi đọc lỗi 400 trả về.
 */
describe('resetPasswordSchema', () => {
  it('chấp nhận khi hai ô khớp nhau và đủ 6 ký tự', () => {
    const result = resetPasswordSchema.safeParse({
      password: 'matkhau123',
      confirmPassword: 'matkhau123',
    })
    expect(result.success).toBe(true)
  })

  it('chặn mật khẩu ngắn hơn 6 ký tự', () => {
    const result = resetPasswordSchema.safeParse({
      password: 'abc12',
      confirmPassword: 'abc12',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['password'])
  })

  it('chặn khi nhập lại không khớp, và báo lỗi ở ĐÚNG ô nhập lại', () => {
    const result = resetPasswordSchema.safeParse({
      password: 'matkhau123',
      confirmPassword: 'matkhau124',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['confirmPassword'])
    expect(result.error?.issues[0]?.message).toBe('Mật khẩu nhập lại không khớp')
  })

  it('không cắt khoảng trắng của mật khẩu', () => {
    // Cố ý KHÔNG `.trim()`: khoảng trắng đầu/cuối là ký tự hợp lệ trong mật
    // khẩu, cắt đi là đổi mật khẩu thành một chuỗi khác chuỗi người dùng gõ.
    const result = resetPasswordSchema.safeParse({
      password: ' matkhau ',
      confirmPassword: ' matkhau ',
    })
    expect(result.success).toBe(true)
    expect(result.data?.password).toBe(' matkhau ')
  })
})
