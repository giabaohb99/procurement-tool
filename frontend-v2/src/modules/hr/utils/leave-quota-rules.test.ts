import { describe, expect, it } from 'vitest'

import { LEAVE_QUOTA_BASIS } from '../types/leave'
import {
  MAX_QUOTA_RULES,
  describeQuotaRule,
  quotaValueOptions,
  sortQuotaRules,
  upsertQuotaRule,
} from './leave-quota-rules'

const ET = LEAVE_QUOTA_BASIS.EMPLOYMENT_TYPE
const JL = LEAVE_QUOTA_BASIS.JOB_LEVEL

describe('leave-quota-rules', () => {
  it('bỏ mã 0 "chưa khai" khỏi ô chọn', () => {
    expect(quotaValueOptions(ET).every((o) => o.value > 0)).toBe(true)
    expect(quotaValueOptions(JL).map((o) => o.label)).toContain('Trưởng phòng')
  })

  it('gọi tên nhóm bằng tiếng Việt', () => {
    expect(describeQuotaRule({ basis: ET, basis_value: 2 })).toBe(
      'Hình thức nhân viên: Bán thời gian',
    )
    expect(describeQuotaRule({ basis: JL, basis_value: 4 })).toBe('Cấp bậc: Trưởng phòng')
  })

  it('xếp hình thức nhân viên trước cấp bậc', () => {
    const sorted = sortQuotaRules([
      { basis: JL, basis_value: 1, quota_days: 1 },
      { basis: ET, basis_value: 3, quota_days: 1 },
      { basis: ET, basis_value: 2, quota_days: 1 },
    ])
    expect(sorted.map((r) => `${r.basis}-${r.basis_value}`)).toEqual(['1-2', '1-3', '2-1'])
  })

  it('cùng nhóm thì ghi đè chứ không thêm dòng trùng', () => {
    const first = upsertQuotaRule([], { basis: ET, basis_value: 2, quota_days: 6 })
    const second = upsertQuotaRule(first.rules, { basis: ET, basis_value: 2, quota_days: 8 })
    expect(second.error).toBeNull()
    expect(second.rules).toEqual([{ basis: ET, basis_value: 2, quota_days: 8 }])
  })

  it('chặn số ngày sai, nhóm chưa chọn và vượt trần dòng', () => {
    expect(upsertQuotaRule([], { basis: ET, basis_value: 2, quota_days: -1 }).error).toMatch(/0 đến 366/)
    expect(upsertQuotaRule([], { basis: ET, basis_value: 2, quota_days: Number.NaN }).error).not.toBeNull()
    expect(upsertQuotaRule([], { basis: ET, basis_value: 0, quota_days: 1 }).error).toMatch(/nhóm/)
    const full = Array.from({ length: MAX_QUOTA_RULES }, (_, i) => ({
      basis: JL,
      basis_value: i + 1,
      quota_days: 1,
    }))
    expect(upsertQuotaRule(full, { basis: ET, basis_value: 2, quota_days: 1 }).error).toMatch(/Tối đa/)
  })
})
