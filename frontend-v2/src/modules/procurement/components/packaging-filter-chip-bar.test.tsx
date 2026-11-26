import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  EMPTY_IMPACT_FILTERS,
  impactFiltersToRequest,
  overviewFiltersToParams,
  type AdvancedFilterVariant,
  type ImpactAdvancedFilters,
} from '../utils/packaging-impact-filters'
import { PackagingFilterChipBar } from './packaging-filter-chip-bar'

/** Giữ bộ lọc trong state như màn thật và ghi lại mọi lần `onChange` để soi thân yêu cầu gửi máy chủ. */
function Harness({
  variant = 'impact',
  initial = EMPTY_IMPACT_FILTERS,
  onChange,
}: {
  variant?: AdvancedFilterVariant
  initial?: ImpactAdvancedFilters
  onChange?: (value: ImpactAdvancedFilters) => void
}) {
  const [value, setValue] = useState(initial)
  const [keyword, setKeyword] = useState('')
  return (
    <PackagingFilterChipBar
      variant={variant}
      value={value}
      onChange={(next) => {
        setValue(next)
        onChange?.(next)
      }}
      keyword={keyword}
      onKeywordChange={setKeyword}
    />
  )
}

const chipGroup = () => screen.getByRole('group', { name: 'Điều kiện lọc đang bật' })

async function openMenu(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: /Thêm điều kiện/ }))
}

afterEach(() => {
  vi.useRealTimers()
})

describe('PackagingFilterChipBar', () => {
  it('shows no chip row until a condition exists and lists the impact fields in the add menu', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    expect(screen.queryByRole('group', { name: 'Điều kiện lọc đang bật' })).not.toBeInTheDocument()
    await openMenu(user)
    const items = screen.getAllByRole('menuitem').map((item) => item.textContent)
    expect(items).toEqual([
      'Xu hướng chi phí',
      'Có mã đã chọn ở vai trò',
      'Quy cách thùng',
      'Tăng/giảm /chai',
      'Tăng/giảm /thùng',
      'CP bao bì/chai mới',
      expect.stringMatching(/^Chỉ sản phẩm có cảnh báo/),
    ])
  })

  it('overview menu has no trend but has the old-cost and % fields', async () => {
    const user = userEvent.setup()
    render(<Harness variant="overview" />)
    await openMenu(user)
    const names = screen.getAllByRole('menuitem').map((item) => item.textContent ?? '')
    expect(names).not.toContain('Xu hướng chi phí')
    expect(names).toEqual(expect.arrayContaining(['CP bao bì/chai cũ', '% chênh', 'Có mã ở vai trò']))
  })

  it('warning text names only current warning kinds (no floor / ceiling)', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await openMenu(user)
    const item = screen.getByRole('menuitem', { name: /Chỉ sản phẩm có cảnh báo/ })
    expect(item).toHaveTextContent('quy cách thùng')
    expect(item).not.toHaveTextContent(/sàn|trần/)
  })

  it('a boolean condition is added immediately as a chip', async () => {
    const user = userEvent.setup()
    const applied: ImpactAdvancedFilters[] = []
    render(<Harness onChange={(next) => applied.push(next)} />)
    await openMenu(user)
    await user.click(screen.getByRole('menuitem', { name: /Chỉ sản phẩm có cảnh báo/ }))
    expect(applied.at(-1)?.warningsOnly).toBe(true)
    expect(within(chipGroup()).getByText('Chỉ SP có cảnh báo')).toBeInTheDocument()
  })

  it('single-choice trend: pick closes the editor and leaves a chip with the label', async () => {
    const user = userEvent.setup()
    const applied: ImpactAdvancedFilters[] = []
    render(<Harness onChange={(next) => applied.push(next)} />)
    await openMenu(user)
    await user.click(screen.getByRole('menuitem', { name: 'Xu hướng chi phí' }))
    await user.click(await screen.findByRole('button', { name: 'Tăng' }))
    expect(applied.at(-1)).toMatchObject({ trend: 'up' })
    expect(within(chipGroup()).getByRole('button', { name: 'Sửa điều kiện: Xu hướng: Tăng' })).toBeInTheDocument()
    expect(screen.queryByRole('group', { name: 'Xu hướng chi phí' })).not.toBeInTheDocument()
  })

  it('multi-choice roles: toggles stay open and the chip lists the labels', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await openMenu(user)
    await user.click(screen.getByRole('menuitem', { name: /Có mã đã chọn ở vai trò/ }))
    await user.click(await screen.findByRole('button', { name: 'Nắp' }))
    await user.click(screen.getByRole('button', { name: 'Chai' }))
    expect(within(chipGroup()).getByText('Vai trò: Chai, Nắp')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Chai' }))
    expect(within(chipGroup()).getByText('Vai trò: Nắp')).toBeInTheDocument()
  })

  it('range: waits 400 ms after typing, then sends the same request fields as before', async () => {
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime })
    vi.useFakeTimers({ shouldAdvanceTime: true })
    const applied: ImpactAdvancedFilters[] = []
    render(<Harness onChange={(next) => applied.push(next)} />)
    await openMenu(user)
    await user.click(screen.getByRole('menuitem', { name: 'Tăng/giảm /thùng' }))
    await user.type(await screen.findByLabelText('Tăng/giảm /thùng từ'), '1.000')
    expect(applied).toHaveLength(0)
    await act(() => vi.advanceTimersByTimeAsync(450))
    expect(applied).toHaveLength(1)
    expect(impactFiltersToRequest(applied[0])).toEqual({ diff_carton_min: 1000 })
    expect(within(chipGroup()).getByText('Tăng/giảm /thùng ≥ 1.000 đ')).toBeInTheDocument()
  })

  it('range: closing the editor before the delay still sends what was typed', async () => {
    const user = userEvent.setup()
    const applied: ImpactAdvancedFilters[] = []
    render(<Harness variant="overview" onChange={(next) => applied.push(next)} />)
    await openMenu(user)
    await user.click(screen.getByRole('menuitem', { name: '% chênh' }))
    await user.type(await screen.findByLabelText('% chênh từ'), '5')
    await user.keyboard('{Escape}')
    expect(overviewFiltersToParams(applied.at(-1)!)).toEqual({ pct_min: 5 })
    expect(within(chipGroup()).getByText('% chênh ≥ 5%')).toBeInTheDocument()
  })

  it('range: shows an inline message for "from" > "to" and does not send the range', async () => {
    const user = userEvent.setup()
    const applied: ImpactAdvancedFilters[] = []
    render(<Harness onChange={(next) => applied.push(next)} />)
    await openMenu(user)
    await user.click(screen.getByRole('menuitem', { name: 'Quy cách thùng' }))
    await user.type(await screen.findByLabelText('Quy cách thùng từ'), '30')
    await user.type(screen.getByLabelText('Quy cách thùng đến'), '10')
    expect(screen.getByRole('alert')).toHaveTextContent('chưa được áp dụng')
    await user.keyboard('{Escape}')
    expect(impactFiltersToRequest(applied.at(-1)!)).toEqual({})
    expect(within(chipGroup()).getByText('Quy cách 30–10 (chưa áp dụng)')).toBeInTheDocument()
  })

  it('an empty new chip disappears when its editor closes without input', async () => {
    const user = userEvent.setup()
    render(<Harness />)
    await openMenu(user)
    await user.click(screen.getByRole('menuitem', { name: 'Tăng/giảm /chai' }))
    expect(await screen.findByText('Tăng/giảm /chai: chưa nhập')).toBeInTheDocument()
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('group', { name: 'Điều kiện lọc đang bật' })).not.toBeInTheDocument()
  })

  it('clicking a chip edits it, the x removes it and the field returns to the menu', async () => {
    const user = userEvent.setup()
    render(
      <Harness
        initial={{ ...EMPTY_IMPACT_FILTERS, roles: [1], cartonQty: { min: '24', max: '40' } }}
        onChange={() => undefined}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'Sửa điều kiện: Quy cách 24–40' }))
    expect(await screen.findByLabelText('Quy cách thùng từ')).toHaveValue('24')
    await user.keyboard('{Escape}')
    await user.click(screen.getByRole('button', { name: 'Bỏ điều kiện Quy cách thùng' }))
    expect(screen.queryByText('Quy cách 24–40')).not.toBeInTheDocument()
    await openMenu(user)
    expect(screen.getByRole('menuitem', { name: 'Quy cách thùng' })).toBeInTheDocument()
    expect(screen.queryByRole('menuitem', { name: /vai trò/ })).not.toBeInTheDocument()
  })
})
