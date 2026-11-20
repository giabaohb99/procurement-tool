import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { PackagingLastPricesToolbar, type LastPricesFilters } from './packaging-last-prices-toolbar'

const GROUPS = [
  { group: 'Chai', count: 12 },
  { group: 'Nắp', count: 3 },
]
const SUPPLIERS = [{ code: 'PHL', name: 'CÔNG TY CỔ PHẦN PHL' }]
const FILTERS: LastPricesFilters = {
  q: '',
  group: '',
  n: 5,
  scope: 'bom',
  suppliers: [],
  from: '',
  to: '',
  trend: 'all',
  minPct: 0,
  onlyPriced: true,
  bomOnly: false,
  showQty: false,
}

function setup(filters: LastPricesFilters = FILTERS) {
  const onChange = vi.fn()
  render(
    <PackagingLastPricesToolbar
      filters={filters}
      groups={GROUPS}
      suppliers={SUPPLIERS}
      onChange={onChange}
    />,
  )
  return { onChange, user: userEvent.setup() }
}

describe('PackagingLastPricesToolbar', () => {
  it('shows a chip per group with its count plus "Tất cả" with the sum', () => {
    setup()
    expect(screen.getByRole('button', { name: 'Tất cả (15)' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Chai (12)' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('selects a group by its exact name (not the label with the count)', async () => {
    const { onChange, user } = setup()
    await user.click(screen.getByRole('button', { name: 'Nắp (3)' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, group: 'Nắp' })
  })

  it('offers 3 / 5 / 10 purchases with 5 selected by default and changes n', async () => {
    const { onChange, user } = setup()
    expect(screen.getByRole('radio', { name: '5 lần' })).toBeChecked()
    expect(screen.getByRole('radio', { name: '3 lần' })).not.toBeChecked()
    await user.click(screen.getByRole('radio', { name: '10 lần' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, n: 10 })
  })

  it('switches the scope between "Định mức + báo giá" and "Mọi mã"', async () => {
    const { onChange, user } = setup()
    expect(screen.getByRole('radio', { name: 'Định mức + báo giá' })).toBeChecked()
    await user.click(screen.getByRole('radio', { name: 'Mọi mã' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, scope: 'all' })
  })

  it('filters the direction of the lần 1 vs lần 2 change', async () => {
    const { onChange, user } = setup()
    expect(screen.getByRole('radio', { name: 'Tất cả' })).toBeChecked()
    await user.click(screen.getByRole('radio', { name: 'Giảm' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, trend: 'down' })
  })

  it('has "Chỉ mã đã có giá" on, "Chỉ mã đang dùng trong định mức" and "Hiện số lượng" off by default', async () => {
    const { onChange, user } = setup()
    expect(screen.getByRole('switch', { name: 'Chỉ mã đã có giá' })).toBeChecked()
    expect(screen.getByRole('switch', { name: 'Chỉ mã đang dùng trong định mức' })).not.toBeChecked()
    expect(screen.getByRole('switch', { name: 'Hiện số lượng' })).not.toBeChecked()
    await user.click(screen.getByRole('switch', { name: 'Hiện số lượng' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, showQty: true })
    await user.click(screen.getByRole('switch', { name: 'Chỉ mã đã có giá' }))
    expect(onChange).toHaveBeenLastCalledWith({ ...FILTERS, onlyPriced: false })
  })

  it('commits the % threshold when leaving the field', async () => {
    const { onChange, user } = setup()
    const input = screen.getByLabelText('Ngưỡng biến động lần 1 so lần 2 (%)')
    await user.click(input)
    await user.type(input, '12,5')
    await user.tab()
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, minPct: 12.5 })
  })
})
