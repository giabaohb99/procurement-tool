import { describe, expect, it } from 'vitest'

import { COST_APPLIES_TO_CODE, COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HrCostItem } from '../types/hr-cost'
import { listOtherCostProblems } from './hr-cost-item-validation'

const M = COST_CALC_METHOD_CODE

const item = (code: string, calc_method: number, over: Partial<HrCostItem> = {}): HrCostItem => ({
  code,
  name: code,
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

const SALARY = item('LUONG', M.PER_HEAD_MONTH)

describe('checks of one «Chi phí khác» row', () => {
  it('a filled row has nothing to say', () => {
    expect(listOtherCostProblems(item('BH', M.PERCENT_OF, { rate: 23.5 }), [SALARY])).toEqual([])
    expect(listOtherCostProblems(item('T13', M.MONTHS_OF, { factor: 1, months: [12] }), [SALARY])).toEqual([])
    expect(listOtherCostProblems(item('Q', M.PER_HEAD_ONCE, { amount: 500_000, months: [3] }), [])).toEqual([])
    //  Cả phòng để trống tháng = chia đều các tháng của kỳ — hợp lệ.
    expect(listOtherCostProblems(item('L', M.LUMP_SUM, { amount: 1 }), [])).toEqual([])
  })

  it('treats 0, negative and blank numbers as not entered', () => {
    expect(listOtherCostProblems(item('BH', M.PERCENT_OF, { rate: 0 }), [SALARY])).toEqual(['Nhập tỷ lệ % lớn hơn 0.'])
    expect(listOtherCostProblems(item('BH', M.PERCENT_OF, { rate: -5 }), [SALARY])).toEqual(['Nhập tỷ lệ % lớn hơn 0.'])
    expect(listOtherCostProblems(item('T', M.MONTHS_OF, { months: [12] }), [SALARY])).toEqual(['Nhập số tháng lương lớn hơn 0.'])
    expect(listOtherCostProblems(item('L', M.LUMP_SUM, { amount: 0 }), [])).toEqual(['Nhập số tiền lớn hơn 0.'])
  })

  it('flags a blank or whitespace-only name', () => {
    expect(listOtherCostProblems(item('L', M.LUMP_SUM, { name: '   ', amount: 1 }), [])).toEqual(['Chưa đặt tên.'])
  })

  it('does not ask a viewer without salary access for an amount they cannot see (backend sends null)', () => {
    expect(listOtherCostProblems(item('Q', M.PER_HEAD_ONCE, { months: [3] }), [], { showMoney: false })).toEqual([])
  })

  it('asks for a month on months-of and once-per-head, and rejects a month outside the plan period', () => {
    expect(listOtherCostProblems(item('Q', M.PER_HEAD_ONCE, { amount: 1 }), [])).toEqual(['Chọn tháng chi.'])
    const q3 = { periodMonths: [7, 8, 9] }
    expect(listOtherCostProblems(item('T', M.MONTHS_OF, { factor: 1, months: [12] }), [SALARY], q3)).toEqual([
      'Tháng chi nằm ngoài kỳ của kế hoạch — chọn lại tháng.',
    ])
    expect(listOtherCostProblems(item('L', M.LUMP_SUM, { amount: 1, months: [2] }), [], q3)).toHaveLength(1)
  })

  it('a percent / months-of row with no salary column left says so — switched-off items do not count', () => {
    const msg = 'Chưa có lương để tính — thêm vị trí và nhập lương ở bảng Người và lương.'
    expect(listOtherCostProblems(item('BH', M.PERCENT_OF, { rate: 10 }), [])).toEqual([msg])
    expect(listOtherCostProblems(item('BH', M.PERCENT_OF, { rate: 10 }), [{ ...SALARY, excluded: true }])).toEqual([msg])
  })

  it('a switched-off row is never checked — it will not be saved', () => {
    expect(listOtherCostProblems(item('X', M.PERCENT_OF, { name: '', excluded: true }), [])).toEqual([])
  })
})
