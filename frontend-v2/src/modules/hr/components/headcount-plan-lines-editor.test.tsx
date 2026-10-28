import { fireEvent, render, screen } from '@testing-library/react'
import type { ComponentProps } from 'react'
import { describe, expect, it, vi } from 'vitest'

import { COST_ACTUAL_SOURCE_CODE, COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import type { HeadcountPlanLine } from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import { buildSubPeriods } from '../utils/headcount-plan-periods'
import { HeadcountPlanLinesEditor } from './headcount-plan-lines-editor'

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
  applies_to: 1,
  position_ids: [],
  months: [],
  actual_source: 0,
  sort_order: 0,
  ...over,
})

const ITEMS = [
  item('LUONG', 'Lương', M.PER_HEAD_MONTH, { actual_source: COST_ACTUAL_SOURCE_CODE.BASE_SALARY }),
  item('PHU_CAP', 'Phụ cấp', M.PER_HEAD_MONTH, { amount: 1_000_000 }),
  item('AN_TRUA', 'Ăn trưa', M.PER_HEAD_MONTH),
  item('BH', 'Bảo hiểm', M.PERCENT_OF, { rate: 23.5 }),
]
const KTV: HeadcountPlanLine = { position_id: 5, position_name: 'Kế toán viên', headcounts: [4, 4, 5, 5], amounts: { LUONG: 12_000_000 }, note: '' }
const STATS = [{ position_id: 5, position_name: 'Kế toán viên', current_count: 4, avg_base_salary: 11_500_000, avg_allowance: null }]

const renderEditor = (over: Partial<ComponentProps<typeof HeadcountPlanLinesEditor>> = {}) => {
  const onChange = vi.fn()
  const onAdd = vi.fn()
  render(
    <HeadcountPlanLinesEditor
      lines={[KTV]}
      periods={buildSubPeriods(1, 1)}
      periodType={1}
      items={ITEMS}
      stats={STATS}
      positions={[{ id: 5, name: 'Kế toán viên' }, { id: 6, name: 'Kế toán trưởng' }]}
      showMoney
      readOnly={false}
      onChange={onChange}
      onAdd={onAdd}
      {...over}
    />,
  )
  return { onChange, onAdd }
}

describe('Người và lương table', () => {
  it('reads Lương/người · Phụ cấp/người and one column per other monthly item — never the % item', () => {
    renderEditor()
    expect(screen.getByText('Lương/người')).toBeInTheDocument()
    expect(screen.getByText('Phụ cấp/người')).toBeInTheDocument()
    expect(screen.getByText('Ăn trưa/người')).toBeInTheDocument()
    expect(screen.queryByText(/Bảo hiểm/)).not.toBeInTheDocument()
  })

  it('shows current staff, needed hires (last period − current) and the current average salary', () => {
    renderEditor()
    expect(screen.getByText('BQ hiện tại 11.500.000')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByLabelText('Lương/người của Kế toán viên')).toHaveValue('12.000.000')
    //  Ô trống = dùng mức chung — chỉ gợi ý, không chép vào dòng.
    expect(screen.getByLabelText('Phụ cấp/người của Kế toán viên')).toHaveAttribute('placeholder', '1.000.000')
  })

  it('builds no money column at all for a viewer who cannot see pay', () => {
    renderEditor({ showMoney: false })
    expect(screen.queryByText('Lương/người')).not.toBeInTheDocument()
    expect(screen.queryByText(/BQ hiện tại/)).not.toBeInTheDocument()
    expect(screen.getByLabelText('Cần có Q1 của Kế toán viên')).toBeInTheDocument()
  })

  it('«Giống nhau cả năm» fills every quarter with one number', () => {
    const { onChange } = renderEditor()
    fireEvent.click(screen.getByRole('button', { name: 'Giống nhau cả năm' }))
    const box = screen.getByLabelText('Số người mọi kỳ của Kế toán viên')
    fireEvent.focus(box)
    fireEvent.change(box, { target: { value: '6' } })
    fireEvent.click(screen.getByRole('button', { name: 'Điền' }))
    expect(onChange).toHaveBeenCalledWith([{ ...KTV, headcounts: [6, 6, 6, 6] }])
  })

  it('the picker only offers positions without a row and adds on a single click', () => {
    const { onAdd } = renderEditor()
    fireEvent.click(screen.getByRole('button', { name: 'Thêm vị trí' }))
    expect(screen.queryByRole('button', { name: 'Kế toán viên' })).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Tìm chức vụ'), { target: { value: 'truong' } })
    fireEvent.click(screen.getByRole('button', { name: 'Kế toán trưởng' }))
    expect(onAdd).toHaveBeenCalledWith(6, 'Kế toán trưởng')
  })

  it('offers «Nhập tổng cả phòng» once, and names the row «Cả phòng (không chia vị trí)»', () => {
    const { onAdd } = renderEditor()
    fireEvent.click(screen.getByRole('button', { name: /Nhập tổng cả phòng/ }))
    expect(onAdd).toHaveBeenCalledWith(0, 'Cả phòng (không chia vị trí)')
  })

  it('an empty table explains what to do with a worked example; read-only has no buttons', () => {
    renderEditor({ lines: [] })
    expect(screen.getByText(/Bấm Thêm vị trí\. Ví dụ Kế toán viên/)).toBeInTheDocument()
    renderEditor({ lines: [], readOnly: true })
    expect(screen.getByText('Kế hoạch chưa có vị trí nào.')).toBeInTheDocument()
  })
})
