import { describe, expect, it } from 'vitest'

import { formatDrilldownCell, resolveDrilldownLink } from './format-drilldown-cell'

describe('formatDrilldownCell', () => {
  it('renders bare dates as dd/MM/yyyy without shifting a day', () => {
    expect(formatDrilldownCell('2026-01-01', 'date')).toBe('01/01/2026')
    expect(formatDrilldownCell('2026-12-31', 'date')).toBe('31/12/2026')
  })

  it('leaves the cell blank for empty or unreadable values instead of printing 0', () => {
    for (const kind of ['text', 'date', 'int', 'days', 'money'] as const) {
      expect(formatDrilldownCell(null, kind)).toBe('')
      expect(formatDrilldownCell(undefined, kind)).toBe('')
      expect(formatDrilldownCell('', kind)).toBe('')
    }
    expect(formatDrilldownCell('not-a-number', 'money')).toBe('')
    expect(formatDrilldownCell('khong-phai-ngay', 'date')).toBe('')
    expect(formatDrilldownCell(12, 'date')).toBe('')
  })

  it('keeps a real zero visible (0 days left is a value, not a blank)', () => {
    expect(formatDrilldownCell(0, 'days')).toBe('0 ngày')
    expect(formatDrilldownCell(0, 'int')).toBe('0')
  })

  it('formats money in full VND and accepts Decimal strings from the API', () => {
    expect(formatDrilldownCell(15_000_000, 'money')).toBe('15.000.000 đ')
    expect(formatDrilldownCell('1500000.00', 'money')).toBe('1.500.000 đ')
  })

  it('formats days with one decimal and negative counts (already overdue)', () => {
    expect(formatDrilldownCell(2.5, 'days')).toBe('2,5 ngày')
    expect(formatDrilldownCell(-12, 'days')).toBe('-12 ngày')
  })

  it('groups thousands for int and never prints [object Object] for text', () => {
    expect(formatDrilldownCell(12345, 'int')).toBe('12.345')
    expect(formatDrilldownCell({ a: 1 }, 'text')).toBe('')
    expect(formatDrilldownCell('NSU001', 'text')).toBe('NSU001')
    expect(formatDrilldownCell(7, 'text')).toBe('7')
  })
})

describe('resolveDrilldownLink', () => {
  it('accepts an internal v2 path', () => {
    expect(resolveDrilldownLink({ link: '/hr/employees/12?tab=labor-contracts' })).toBe(
      '/hr/employees/12?tab=labor-contracts',
    )
  })

  it('refuses external, protocol-relative and script links coming from row data', () => {
    expect(resolveDrilldownLink({ link: 'https://evil.example/x' })).toBeNull()
    expect(resolveDrilldownLink({ link: '//evil.example/x' })).toBeNull()
    expect(resolveDrilldownLink({ link: '/\\evil.example' })).toBeNull()
    expect(resolveDrilldownLink({ link: 'javascript:alert(1)' })).toBeNull()
    expect(resolveDrilldownLink({ link: '' })).toBeNull()
    expect(resolveDrilldownLink({ link: null })).toBeNull()
    expect(resolveDrilldownLink({})).toBeNull()
  })
})
