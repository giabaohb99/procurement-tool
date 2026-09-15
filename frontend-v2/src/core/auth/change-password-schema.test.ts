import { describe, expect, it } from 'vitest'

import { changePasswordSchema } from './change-password-schema'

const ok = {
  oldPassword: 'matkhaucu1',
  newPassword: 'matkhaumoi1',
  confirmPassword: 'matkhaumoi1',
}

describe('changePasswordSchema', () => {
  it('accepts a valid triple', () => {
    expect(changePasswordSchema.safeParse(ok).success).toBe(true)
  })

  it('requires the current password', () => {
    const result = changePasswordSchema.safeParse({ ...ok, oldPassword: '' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['oldPassword'])
  })

  it('rejects a new password shorter than the policy minimum', () => {
    const result = changePasswordSchema.safeParse({
      ...ok,
      newPassword: 'abc123',
      confirmPassword: 'abc123',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['newPassword'])
  })

  it('rejects a new password with letters only — bao-CR-405 requires a digit too', () => {
    const result = changePasswordSchema.safeParse({
      ...ok,
      newPassword: 'matkhaumoi',
      confirmPassword: 'matkhaumoi',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues.some((i) => i.path[0] === 'newPassword')).toBe(true)
  })

  it('rejects a mismatched confirmation', () => {
    const result = changePasswordSchema.safeParse({ ...ok, confirmPassword: 'khackhac1' })
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]?.path).toEqual(['confirmPassword'])
  })

  it('rejects reusing the current password — the backend refuses this case as well', () => {
    const result = changePasswordSchema.safeParse({
      oldPassword: 'matkhaucu1',
      newPassword: 'matkhaucu1',
      confirmPassword: 'matkhaucu1',
    })
    expect(result.success).toBe(false)
    expect(result.error?.issues.some((i) => i.path[0] === 'newPassword')).toBe(true)
  })
})
