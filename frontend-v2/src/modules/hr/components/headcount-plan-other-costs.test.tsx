import { fireEvent, render, screen } from '@testing-library/react'
import type { ComponentProps } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { COST_APPLIES_TO_CODE, COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HrCostItem } from '../types/hr-cost'
import { HeadcountPlanOtherCosts } from './headcount-plan-other-costs'

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

const ITEMS = [
  item('LUONG', 'Lương', M.PER_HEAD_MONTH),
  item('PHU_CAP', 'Phụ cấp', M.PER_HEAD_MONTH),
  item('BH', 'Bảo hiểm', M.PERCENT_OF, { rate: 23.5, cap_amount: 50_600_000, base_codes: ['LUONG', 'PHU_CAP'] }),
  item('T13', 'Thưởng tháng 13', M.MONTHS_OF, { factor: 1, base_codes: ['LUONG'], months: [12] }),
  item('QUA', 'Quà 8/3', M.PER_HEAD_ONCE, { amount: 500_000, months: [3] }),
]

const renderBlock = (over: Partial<ComponentProps<typeof HeadcountPlanOtherCosts>> = {}) => {
  const onChange = vi.fn()
  render(
    <HeadcountPlanOtherCosts
      items={ITEMS}
      onChange={onChange}
      groups={[]}
      positions={[{ id: 7, name: 'Kế toán trưởng' }]}
      periodMonths={Array.from({ length: 12 }, (_, i) => i + 1)}
      periodLabel="2026"
      skipped={[]}
      showMoney
      readOnly={false}
      {...over}
    />,
  )
  return { onChange }
}

describe('Chi phí khác — one editable sentence per cost', () => {
  it('lists only non-monthly costs, each as a sentence with its number in place', () => {
    renderBlock()
    expect(screen.queryByDisplayValue('Lương')).not.toBeInTheDocument()
    expect(screen.getByDisplayValue('Bảo hiểm')).toBeInTheDocument()
    expect(screen.getByText('% trên lương + phụ cấp')).toBeInTheDocument()
    expect(screen.getByLabelText('Tỷ lệ % của Bảo hiểm')).toHaveValue('23,5')
    expect(screen.getByText('(tối đa 50.600.000 đ/người)')).toBeInTheDocument()
    expect(screen.getByLabelText('Số tiền mỗi người của Quà 8/3')).toHaveValue('500.000')
  })

  it('unticking keeps the row (can be ticked back) but marks it to be dropped on save', () => {
    const { onChange } = renderBlock()
    fireEvent.click(screen.getByRole('checkbox', { name: 'Dùng Quà 8/3' }))
    const next = onChange.mock.calls[0][0] as HrCostItem[]
    expect(next.find((i) => i.code === 'QUA')?.excluded).toBe(true)
    expect(next).toHaveLength(ITEMS.length)
  })

  it('editing the name only renames — the hidden code stays (it keys the saved numbers)', () => {
    const { onChange } = renderBlock()
    fireEvent.change(screen.getByDisplayValue('Quà 8/3'), { target: { value: 'Quà Tết' } })
    expect((onChange.mock.calls[0][0] as HrCostItem[]).find((i) => i.name === 'Quà Tết')?.code).toBe('QUA')
  })

  it('an old cost the sentence cannot show is read out and kept as is', () => {
    renderBlock({
      items: [...ITEMS, item('RIENG', 'Phụ cấp độc hại', M.PER_HEAD_ONCE, { amount: 1, months: [6], applies_to: 2, position_ids: [7], custom_parts: ['applies'] })],
    })
    expect(screen.getByText('giữ nguyên')).toBeInTheDocument()
    expect(screen.getByText(/chỉ vị trí: Kế toán trưởng/)).toBeInTheDocument()
  })

  it('a viewer without salary access sees the costs, hidden amounts, and cannot edit them', () => {
    renderBlock({ showMoney: false, lockedReason: 'Cần quyền xem lương của pháp nhân này để sửa chi phí.' })
    expect(screen.getByText('Cần quyền xem lương của pháp nhân này để sửa chi phí.')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.getAllByText('(ẩn số tiền)')).toHaveLength(1)
    expect(screen.queryByText(/50\.600\.000/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Thêm chi phí/ })).not.toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: 'Dùng Quà 8/3' })).toBeDisabled()
  })

  it('shows what is missing right under the row', () => {
    renderBlock({ items: [...ITEMS.slice(0, 2), item('DL', 'Du lịch', M.LUMP_SUM, { applies_to: 3 })] })
    expect(screen.getByText('Nhập số tiền lớn hơn 0.')).toBeInTheDocument()
  })

  it('an empty block says what to add', () => {
    renderBlock({ items: ITEMS.slice(0, 2) })
    expect(screen.getByText(/Chưa có chi phí nào ngoài lương/)).toBeInTheDocument()
  })
})
