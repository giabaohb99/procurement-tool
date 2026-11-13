import { describe, expect, it } from 'vitest'

import { buildConcurrentCompanyOptions } from './concurrent-company-options'

const COMPANIES = [
  { id: 1, name: 'DEGO HOLDING' },
  { id: 2, name: 'IDA GLOBAL' },
  { id: 13, name: 'SAM GROUP' },
]

describe('buildConcurrentCompanyOptions (duoc-CR-756)', () => {
  it('every company except the current one (backend 400 "trùng công ty chính"), sorted by name', () => {
    expect(buildConcurrentCompanyOptions(COMPANIES, 1).map((o) => o.label)).toEqual(['IDA GLOBAL', 'SAM GROUP'])
  })

  it('editing a row whose company became the current one keeps it, so the picker never shows blank', () => {
    expect(buildConcurrentCompanyOptions(COMPANIES, 13, 13).map((o) => o.id)).toEqual([1, 2, 13])
  })

  it('profile without a primary company (0) lists everything; empty catalogue gives empty list', () => {
    expect(buildConcurrentCompanyOptions(COMPANIES, 0)).toHaveLength(3)
    expect(buildConcurrentCompanyOptions([], 1)).toEqual([])
  })
})
