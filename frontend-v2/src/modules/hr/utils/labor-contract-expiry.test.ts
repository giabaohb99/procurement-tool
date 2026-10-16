import { describe, expect, it } from 'vitest'

import type { ExpiringLaborContract } from '../types/labor-contract'
import { countByLevel, describeDaysLeft } from './labor-contract-expiry'

function contract(days_left: number, level: 'danger' | 'warn'): ExpiringLaborContract {
  return {
    id: days_left + 1000,
    code: 'HDLD001',
    contract_no: '',
    contract_type: 2,
    employee_id: 1,
    employee_code: 'NV01',
    employee_name: 'Nguyễn Văn A',
    end_date: '2026-10-30',
    days_left,
    level,
  }
}

describe('describeDaysLeft', () => {
  it('says overdue with a positive day count, never "-3 ngày"', () => {
    expect(describeDaysLeft(-3)).toBe('Quá hạn 3 ngày')
    expect(describeDaysLeft(-1)).toBe('Quá hạn 1 ngày')
  })

  it('treats the last day as "today", not "còn 0 ngày"', () => {
    expect(describeDaysLeft(0)).toBe('Hết hạn hôm nay')
  })

  it('counts the days left otherwise', () => {
    expect(describeDaysLeft(1)).toBe('Còn 1 ngày')
    expect(describeDaysLeft(30)).toBe('Còn 30 ngày')
  })
})

describe('countByLevel', () => {
  it('returns zeros for an empty list', () => {
    expect(countByLevel([])).toEqual({ total: 0, overdue: 0, danger: 0, warn: 0 })
  })

  it('trusts the level from the backend instead of recomputing it from days', () => {
    //  15 ngày là mức đỏ theo backend (mốc báo trước của Điều 45) — giao diện không tự vạch ngưỡng.
    const items = [contract(-2, 'danger'), contract(0, 'danger'), contract(15, 'danger'), contract(20, 'warn')]
    expect(countByLevel(items)).toEqual({ total: 4, overdue: 1, danger: 3, warn: 1 })
  })
})
