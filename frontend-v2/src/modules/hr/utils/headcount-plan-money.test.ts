import { describe, expect, it } from 'vitest'

import { resolveCanSeeMoney } from './headcount-plan-money'

const shown = { money_hidden: false, total: { values: [1], total: 1 } }
const masked = { money_hidden: true, total: null }

describe('who sees plan money', () => {
  it('never shows money without labor_contract.read, whatever the server says', () => {
    expect(resolveCanSeeMoney(false, { can_see_money: true }, shown)).toBe(false)
  })

  it('follows the preview first — it reflects the company currently picked on the form', () => {
    //  Kế hoạch lưu ở pháp nhân A (xem được) nhưng form vừa đổi sang B (bị che): phải ẩn theo B.
    expect(resolveCanSeeMoney(true, { can_see_money: true }, masked)).toBe(false)
    expect(resolveCanSeeMoney(true, { can_see_money: false }, shown)).toBe(true)
  })

  it('treats a null total as masked even if the flag is missing (older server)', () => {
    expect(resolveCanSeeMoney(true, undefined, { total: null })).toBe(false)
  })

  it('falls back to the detail flag, then to showing, when there is no preview yet', () => {
    expect(resolveCanSeeMoney(true, { can_see_money: false }, undefined)).toBe(false)
    expect(resolveCanSeeMoney(true, { can_see_money: true }, null)).toBe(true)
    expect(resolveCanSeeMoney(true, undefined, undefined)).toBe(true)
  })
})
