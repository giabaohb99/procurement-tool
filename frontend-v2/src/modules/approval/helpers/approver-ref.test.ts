import { describe, expect, it } from 'vitest'

import { APPROVER_KIND } from '../types/approval'
import { danhSachId, ghepId, refAfterKindChange, visibleApproverKinds } from './approver-ref'

describe('refAfterKindChange', () => {
  it('fills the flow entity as the permission key when switching to «Người có quyền duyệt»', () => {
    expect(refAfterKindChange(APPROVER_KIND.permission, APPROVER_KIND.permission, 'vehicle_booking')).toBe(
      'vehicle_booking',
    )
  })

  it('clears the ref for every other kind so an old employee id is never read as a role code', () => {
    for (const kind of Object.values(APPROVER_KIND).filter((k) => k !== APPROVER_KIND.permission)) {
      expect(refAfterKindChange(kind, APPROVER_KIND.permission, 'vehicle_booking')).toBe('')
    }
  })

  it('keeps the permission kind distinct from every older kind', () => {
    const values = Object.values(APPROVER_KIND)
    expect(new Set(values).size).toBe(values.length)
    expect(APPROVER_KIND.permission).toBe(9)
  })
})

describe('danhSachId / ghepId', () => {
  it('drops junk, zero and negative ids instead of breaking the whole field', () => {
    expect(danhSachId(' 12, ,abc,-3,0,15,')).toEqual([12, 15])
    expect(danhSachId(undefined)).toEqual([])
    expect(ghepId(danhSachId('12,15'))).toBe('12,15')
  })
})

describe('visibleApproverKinds', () => {
  const kinds = [1, 2, 8, 9].map((value) => ({ value, label: `k${value}` }))
  const supported = ['vehicle_booking', 'leave_request', 'room_booking']

  it('offers «Người có quyền duyệt» only on flows of a supported entity', () => {
    expect(visibleApproverKinds(kinds, 9, 'vehicle_booking', supported, 1).map((k) => k.value)).toEqual([1, 2, 8, 9])
    expect(visibleApproverKinds(kinds, 9, 'document', supported, 1).map((k) => k.value)).toEqual([1, 2, 8])
    expect(visibleApproverKinds(kinds, 9, 'seal_request', supported, undefined).map((k) => k.value)).toEqual([
      1, 2, 8,
    ])
  })

  it('hides it when an older backend sends no supported list, instead of offering a choice that 422s', () => {
    expect(visibleApproverKinds(kinds, 9, 'vehicle_booking', undefined, 1).map((k) => k.value)).toEqual([1, 2, 8])
    expect(visibleApproverKinds(kinds, 9, 'vehicle_booking', [], 1).map((k) => k.value)).toEqual([1, 2, 8])
  })

  it('keeps the choice for a step already saved with it so the select never shows blank', () => {
    expect(visibleApproverKinds(kinds, 9, 'document', supported, 9).map((k) => k.value)).toEqual([1, 2, 8, 9])
  })

  it('returns nothing for an empty kinds list', () => {
    expect(visibleApproverKinds([], 9, 'vehicle_booking', supported, 9)).toEqual([])
  })
})
