import { describe, expect, it } from 'vitest'

import { COST_APPLIES_TO_CODE, COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HrCostItem } from '../types/hr-cost'
import { describeCostItem, HIDDEN_MONEY_TEXT } from './hr-cost-item-describe'

const M = COST_CALC_METHOD_CODE

const item = (code: string, name: string, calc_method: number, over: Partial<HrCostItem> = {}): HrCostItem => ({
  code,
  name,
  group_id: 1,
  calc_method,
  rate: null,
  factor: null,
  cap_amount: null,
  amount: null,
  base_codes: [],
  applies_to: COST_APPLIES_TO_CODE.ALL_POSITIONS,
  position_ids: [],
  months: [],
  actual_source: 0,
  sort_order: 0,
  ...over,
})

const SALARY = item('LUONG', 'Lương', M.PER_HEAD_MONTH)
const ALLOWANCE = item('PC', 'Phụ cấp', M.PER_HEAD_MONTH)
const ALL = [SALARY, ALLOWANCE]
const money = { showMoney: true }

describe('one-line description of a cost item', () => {
  it('per head per month without a common rate points the user to the position table', () => {
    expect(describeCostItem(SALARY, ALL, money)).toBe('Nhập số tiền theo từng vị trí')
    expect(describeCostItem({ ...SALARY, amount: 0 }, ALL, money)).toBe('Nhập số tiền theo từng vị trí')
  })

  it('per head per month with a common rate reads it out and says positions may differ', () => {
    expect(describeCostItem({ ...ALLOWANCE, amount: 730_000 }, ALL, money)).toBe(
      '730.000 đ/người/tháng · vị trí nhập riêng nếu khác',
    )
  })

  it('masks the common rate for viewers without salary access (backend sends null)', () => {
    expect(describeCostItem({ ...ALLOWANCE, amount: null }, ALL, { showMoney: false })).toBe(
      `${HIDDEN_MONEY_TEXT} · nhập theo từng vị trí`,
    )
  })

  it('percent lists the bases by name, the cap, and stays silent on months when it is every month', () => {
    const bh = item('BH', 'BH', M.PERCENT_OF, { rate: 17.5, base_codes: ['LUONG', 'PC'], cap_amount: 46_800_000 })
    expect(describeCostItem(bh, [...ALL, bh], money)).toBe('17,5% × (Lương + Phụ cấp), tối đa 46.800.000 đ/người')
  })

  it('percent with no cap (0) does not mention a maximum; a single base has no parentheses', () => {
    const kpcd = item('KPCD', 'KPCĐ', M.PERCENT_OF, { rate: 2, base_codes: ['LUONG'], cap_amount: 0, months: [6, 3] })
    expect(describeCostItem(kpcd, ALL, money)).toBe('2% × Lương, chi vào T3, T6')
  })

  it('months-of reads as «1 tháng × Lương, chi vào T12»', () => {
    const t13 = item('T13', 'Thưởng tháng 13', M.MONTHS_OF, { factor: 1, base_codes: ['LUONG'], months: [12] })
    expect(describeCostItem(t13, ALL, money)).toBe('1 tháng × Lương, chi vào T12')
  })

  it('once per head names the selected positions, at most two then a count', () => {
    const gift = item('QUA', 'Quà', M.PER_HEAD_ONCE, {
      amount: 500_000,
      months: [3],
      applies_to: COST_APPLIES_TO_CODE.SELECTED_POSITIONS,
      position_ids: [1, 2, 3],
    })
    const positions = [
      { id: 1, name: 'Kế toán' },
      { id: 2, name: 'Thủ kho' },
      { id: 3, name: 'Lái xe' },
    ]
    expect(describeCostItem(gift, ALL, { showMoney: true, positions })).toBe(
      '500.000 đ/người, chi vào T3, chỉ vị trí: Kế toán, Thủ kho và 1 vị trí khác',
    )
    expect(describeCostItem(gift, ALL, { showMoney: true })).toContain('chỉ 3 vị trí đã chọn')
  })

  it('lump sum spreads evenly when no month is picked', () => {
    expect(describeCostItem(item('DL', 'Du lịch', M.LUMP_SUM, { amount: 50_000_000 }), ALL, money)).toBe(
      '50.000.000 đ cả phòng, chia đều các tháng',
    )
    expect(describeCostItem(item('DL', 'Du lịch', M.LUMP_SUM, { amount: 50_000_000, months: [6] }), ALL, money)).toBe(
      '50.000.000 đ cả phòng, chi vào T6',
    )
  })

  it('masks every amount but keeps the rate when money is hidden (backend sends null)', () => {
    const bh = item('BH', 'BH', M.PERCENT_OF, { rate: 23.5, base_codes: ['LUONG'], cap_amount: null })
    expect(describeCostItem(bh, ALL, { showMoney: false })).toBe('23,5% × Lương')
    const gift = item('QUA', 'Quà', M.PER_HEAD_ONCE, { amount: null, months: [3] })
    expect(describeCostItem(gift, ALL, { showMoney: false })).toBe(`${HIDDEN_MONEY_TEXT}/người, chi vào T3`)
    expect(describeCostItem(gift, ALL, { showMoney: false })).not.toMatch(/\d{3}\.\d{3}/)
  })

  it('says what is missing instead of rendering an empty formula', () => {
    expect(describeCostItem(item('P', 'P', M.PERCENT_OF, { rate: 0 }), ALL, money)).toBe('0% × (chưa chọn khoản)')
    expect(describeCostItem(item('Q', 'Q', M.PER_HEAD_ONCE, { amount: 0 }), ALL, money)).toBe(
      '0 đ/người, chưa chọn tháng chi',
    )
  })

  it('shows the raw code of a base that no longer exists, and survives an unknown method', () => {
    const p = item('P', 'P', M.PERCENT_OF, { rate: 10, base_codes: ['DA_XOA'] })
    expect(describeCostItem(p, ALL, money)).toBe('10% × DA_XOA')
    expect(describeCostItem(item('X', 'X', 99), ALL, money)).toBe('Cách tính chưa hỗ trợ')
  })
})
