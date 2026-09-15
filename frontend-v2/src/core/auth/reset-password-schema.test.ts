import { describe, expect, it } from 'vitest'

import { resetPasswordSchema } from './reset-password-schema'

/**
 * Màn đặt lại mật khẩu là màn CÔNG KHAI — ai cầm được đường dẫn cũng mở được.
 * Các khẳng định dưới đây giữ đúng phần kiểm tra tại chỗ, để lỗi hiện ngay dưới
 * ô nhập thay vì phải gọi API rồi đọc lỗi 400 trả về.
 */
describe('resetPasswordSchema', () => {
  it('accepts a matching pair that satisfies the policy', () => {
    const result = resetPasswordSchema.safeParse({
      password: 'matkhau123',
      confirmPassword: 'matkhau123',
    })
    expect(result.success).toBe(true)
  })

  it('rejects a password shorter than the policy minimum', () => {
    const result = resetPasswordSchema.safeParse({
      password: 'abc123',
      confirmPassword: 'abc123',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['password'])
  })

  it('rejects a password with no digit', () => {
    const result = resetPasswordSchema.safeParse({
      password: 'matkhaumoi',
      confirmPassword: 'matkhaumoi',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['password'])
  })

  it('rejects a mismatched confirmation, and flags the confirmation field itself', () => {
    const result = resetPasswordSchema.safeParse({
      password: 'matkhau123',
      confirmPassword: 'matkhau124',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['confirmPassword'])
    expect(result.error?.issues[0]?.message).toBe('Mật khẩu nhập lại không khớp')
  })

  it('rejects surrounding whitespace instead of trimming it away', () => {
    // bao-CR-405: bản cũ nhận ' matkhau ' nguyên vẹn vì cắt đi là đổi mật khẩu thành
    // một chuỗi khác chuỗi người dùng gõ. Nay backend TỪ CHỐI thẳng ca đó — người
    // dùng gõ dư dấu cách sẽ không bao giờ đăng nhập lại được bằng cái họ nhớ.
    const result = resetPasswordSchema.safeParse({
      password: ' matkhau1 ',
      confirmPassword: ' matkhau1 ',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['password'])
  })
})
