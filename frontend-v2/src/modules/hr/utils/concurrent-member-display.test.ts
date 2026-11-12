import { describe, expect, it } from 'vitest'

import { formatConcurrentPeriod, formatPrimaryPlace, needsStatusBadge } from './concurrent-member-display'

describe('formatConcurrentPeriod', () => {
  it('shows both ends, only the start when open-ended, only the end for old rows without a start', () => {
    expect(formatConcurrentPeriod('2026-09-01', '2026-09-30')).toBe('01/09/2026 – 30/09/2026')
    expect(formatConcurrentPeriod('2026-09-01', null)).toBe('Từ 01/09/2026')
    expect(formatConcurrentPeriod(null, '2026-09-30')).toBe('Đến 30/09/2026')
  })

  it('does not print an empty string when both dates are missing', () => {
    expect(formatConcurrentPeriod(null, null)).toBe('Chưa rõ ngày')
  })

  it('treats an empty string like a missing date instead of printing Invalid Date', () => {
    expect(formatConcurrentPeriod('', '')).toBe('Chưa rõ ngày')
  })
})

describe('formatPrimaryPlace', () => {
  it('joins department and company, dropping the missing side', () => {
    expect(formatPrimaryPlace({ primary_department_name: 'Phòng Kế toán', primary_company_name: 'Công ty A' })).toBe(
      'Phòng Kế toán — Công ty A',
    )
    expect(formatPrimaryPlace({ primary_department_name: '', primary_company_name: 'Công ty A' })).toBe('Công ty A')
    expect(formatPrimaryPlace({ primary_department_name: '', primary_company_name: '' })).toBe('')
  })
})

describe('needsStatusBadge', () => {
  it('only flags rows that are not currently in effect', () => {
    expect(needsStatusBadge({ status: 2 })).toBe(false)
    expect(needsStatusBadge({ status: 1 })).toBe(true)
    expect(needsStatusBadge({ status: 3 })).toBe(true)
  })
})
