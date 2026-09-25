import { describe, expect, it } from 'vitest'

import { defaultItemGroups, hasAvailableLinesCriteria, isLineGroupOnly } from './survey-process-filter'

describe('survey-process-filter — bao-CR-487', () => {
  it('opens on the line group only, and on nothing when the line has no group', () => {
    expect(defaultItemGroups('Nhãn')).toEqual(['Nhãn'])
    expect(defaultItemGroups('  ')).toEqual([])
    expect(defaultItemGroups(null)).toEqual([])
  })

  it('needs at least one criterion — whitespace-only keyword does not count', () => {
    expect(hasAvailableLinesCriteria({ supplierCodes: [], itemGroups: [], search: '   ' })).toBe(false)
    expect(hasAvailableLinesCriteria({ supplierCodes: ['NCC-A'], itemGroups: [], search: '' })).toBe(true)
    expect(hasAvailableLinesCriteria({ supplierCodes: [], itemGroups: ['Nhãn'], search: '' })).toBe(true)
    expect(hasAvailableLinesCriteria({ supplierCodes: [], itemGroups: [], search: 'x' })).toBe(true)
  })

  it('hides «Về phân loại dòng» only when the box holds exactly the line group', () => {
    expect(isLineGroupOnly(['Nhãn'], 'Nhãn')).toBe(true)
    expect(isLineGroupOnly(['Nhãn', 'Thùng'], 'Nhãn')).toBe(false)
    expect(isLineGroupOnly([], 'Nhãn')).toBe(false)
    // Dòng không có phân loại: ô rỗng là «đúng như dòng», chọn gì đó thì không.
    expect(isLineGroupOnly([], '')).toBe(true)
    expect(isLineGroupOnly(['Nhãn'], '')).toBe(false)
  })
})
