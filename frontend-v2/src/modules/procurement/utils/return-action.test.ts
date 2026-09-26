// bao-CR-498 — một nút «Trả về» phải đi đúng đường theo hai cờ backend, không đoán.
import { describe, expect, it } from 'vitest'

import { resolveReturnAction } from './return-action'

describe('resolveReturnAction', () => {
  it('asks the user only when BOTH paths are open', () => {
    expect(resolveReturnAction(true, true)).toBe('choose')
  })

  it('goes straight to the single open path', () => {
    expect(resolveReturnAction(true, false)).toBe('requester')
    expect(resolveReturnAction(false, true)).toBe('department')
  })

  it('hides the button when no path is open', () => {
    expect(resolveReturnAction(false, false)).toBeNull()
  })
})
