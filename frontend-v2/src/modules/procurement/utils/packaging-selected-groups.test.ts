import { describe, expect, it } from 'vitest'

import { buildSelectedGroupChips, resolveSelectedGroup } from './packaging-selected-groups'

describe('buildSelectedGroupChips', () => {
  it('returns nothing for an empty or not-yet-loaded list', () => {
    expect(buildSelectedGroupChips(undefined)).toEqual([])
    expect(buildSelectedGroupChips([])).toEqual([])
  })

  it('counts per group and orders by packaging role, unknown groups last in first-seen order', () => {
    const rows = ['Thùng', 'Khác', 'Chai', 'Zeta', 'Chai', 'Nhãn thùng', 'Nắp', 'Nhãn'].map((group) => ({ group }))
    expect(buildSelectedGroupChips(rows)).toEqual([
      { group: 'Chai', count: 2 },
      { group: 'Nắp', count: 1 },
      { group: 'Nhãn', count: 1 },
      { group: 'Nhãn thùng', count: 1 },
      { group: 'Thùng', count: 1 },
      { group: 'Khác', count: 1 },
      { group: 'Zeta', count: 1 },
    ])
  })
})

describe('resolveSelectedGroup', () => {
  const chips = [{ group: 'Chai', count: 1 }]
  it('keeps a group that is still present and resets one that vanished (or empty) to all', () => {
    expect(resolveSelectedGroup('Chai', chips)).toBe('Chai')
    expect(resolveSelectedGroup('Nắp', chips)).toBe('')
    expect(resolveSelectedGroup('', chips)).toBe('')
    expect(resolveSelectedGroup('Chai', [])).toBe('')
  })
})
