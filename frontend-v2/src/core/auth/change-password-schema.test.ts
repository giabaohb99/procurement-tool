import { describe, expect, it } from 'vitest'

import { changePasswordSchema } from './change-password-schema'

const ok = {
  oldPassword: 'matkhaucu',
  newPassword: 'matkhaumoi',
  confirmPassword: 'matkhaumoi',
}

describe('changePasswordSchema', () => {
  it('chấp nhận bộ ba hợp lệ', () => {
    expect(changePasswordSchema.safeParse(ok).success).toBe(true)
  })

  it('bắt buộc nhập mật khẩu hiện tại', () => {
    const result = changePasswordSchema.safeParse({ ...ok, oldPassword: '' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['oldPassword'])
  })

  it('chặn mật khẩu mới ngắn hơn 6 ký tự', () => {
    const result = changePasswordSchema.safeParse({
      ...ok,
      newPassword: 'abc12',
      confirmPassword: 'abc12',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['newPassword'])
  })

  it('chặn khi nhập lại không khớp', () => {
    const result = changePasswordSchema.safeParse({ ...ok, confirmPassword: 'khackhac' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['confirmPassword'])
  })

  it('chặn mật khẩu mới trùng mật khẩu cũ — backend cũng từ chối ca này', () => {
    const result = changePasswordSchema.safeParse({
      oldPassword: 'matkhaucu',
      newPassword: 'matkhaucu',
      confirmPassword: 'matkhaucu',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues.some((i) => i.path[0] === 'newPassword')).toBe(true)
  })
})
