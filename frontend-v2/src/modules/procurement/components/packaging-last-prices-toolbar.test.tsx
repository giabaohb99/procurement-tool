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
  groups: [],
  n: 5,
  scope: 'all',
  suppliers: [],
  from: '',
  to: '',
  trend: 'all',
  minPct: 0,
  onlyPriced: false,
  bomOnly: false,
  showQty: false,
  all: false,
  trendAllLit: false,
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
  it('shows a chip per group with its count, none active and "Tất cả" not lit until clicked', () => {
    setup()
    expect(screen.getByRole('button', { name: 'Tất cả' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('button', { name: 'Chai (12)' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('button', { name: 'Nắp (3)' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('toggles a group on by its exact name (not the label with the count)', async () => {
    const { onChange, user } = setup()
    await user.click(screen.getByRole('button', { name: 'Nắp (3)' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, groups: ['Nắp'], all: false })
  })

  it('"Tất cả" clears the group chips, lights up and loads everything; a group chip then unlights it', async () => {
    const first = setup({ ...FILTERS, groups: ['Nắp'] })
    await first.user.click(screen.getByRole('button', { name: 'Tất cả' }))
    expect(first.onChange).toHaveBeenCalledWith({ ...FILTERS, groups: [], all: true })
  })

  it('shows "Tất cả" lit when all is on, and the recent-mode caption only in recent mode', async () => {
    render(
      <PackagingLastPricesToolbar filters={{ ...FILTERS, all: true }} groups={GROUPS} suppliers={SUPPLIERS} onChange={vi.fn()} />,
    )
    expect(screen.getByRole('button', { name: 'Tất cả' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.queryByText(/mã mua gần nhất/)).not.toBeInTheDocument()
  })

  it('allows several groups at once, appends in click order and clicking an active chip switches it off', async () => {
    const { onChange, user } = setup({ ...FILTERS, groups: ['Nắp', 'Chai'] })
    expect(screen.getByRole('button', { name: 'Nắp (3)' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Chai (12)' })).toHaveAttribute('aria-pressed', 'true')
    await user.click(screen.getByRole('button', { name: 'Chai (12)' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, groups: ['Nắp'], all: false })
  })

  it('appends a second group after the first', async () => {
    const { onChange, user } = setup({ ...FILTERS, groups: ['Nắp'] })
    await user.click(screen.getByRole('button', { name: 'Chai (12)' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, groups: ['Nắp', 'Chai'], all: false })
  })

  it('keeps an active group visible (count 0) when the server no longer lists it, so it can be switched off', async () => {
    const { onChange, user } = setup({ ...FILTERS, groups: ['Nhãn'] })
    const chip = screen.getByRole('button', { name: 'Nhãn (0)' })
    expect(chip).toHaveAttribute('aria-pressed', 'true')
    await user.click(chip)
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, groups: [], all: false })
  })

  it('offers 3 / 5 / 10 purchases with 5 selected by default and changes n', async () => {
    const { onChange, user } = setup()
    expect(screen.getByRole('radio', { name: '5 lần' })).toBeChecked()
    expect(screen.getByRole('radio', { name: '3 lần' })).not.toBeChecked()
    await user.click(screen.getByRole('radio', { name: '10 lần' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, n: 10 })
  })

  it('switches the scope between "Mọi mã" (default) and "Định mức + báo giá"', async () => {
    const { onChange, user } = setup()
    expect(screen.getByRole('radio', { name: 'Mọi mã' })).toBeChecked()
    expect(screen.getByRole('radio', { name: 'Định mức + báo giá' })).not.toBeChecked()
    await user.click(screen.getByRole('radio', { name: 'Định mức + báo giá' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, scope: 'bom' })
  })

  it('filters the direction of the lần 1 vs lần 2 change; its "Tất cả" is not lit on open and lights after a click', async () => {
    const { onChange, user } = setup()
    expect(screen.getByRole('radio', { name: 'Tất cả' })).not.toBeChecked()
    expect(screen.getByRole('radio', { name: 'Giảm' })).not.toBeChecked()
    await user.click(screen.getByRole('radio', { name: 'Giảm' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, trend: 'down', trendAllLit: false })
    await user.click(screen.getByRole('radio', { name: 'Tất cả' }))
    expect(onChange).toHaveBeenLastCalledWith({ ...FILTERS, trend: 'all', trendAllLit: true })
  })

  it('clicking the active direction again switches it off', async () => {
    const { onChange, user } = setup({ ...FILTERS, trend: 'up' })
    expect(screen.getByRole('radio', { name: 'Tăng' })).toBeChecked()
    await user.click(screen.getByRole('radio', { name: 'Tăng' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, trend: 'all', trendAllLit: false })
  })

  it('has every switch off by default ("Chỉ mã đã có giá", "Chỉ mã đang dùng trong định mức", "Hiện số lượng")', async () => {
    const { onChange, user } = setup()
    expect(screen.getByRole('switch', { name: 'Chỉ mã đã có giá' })).not.toBeChecked()
    expect(screen.getByRole('switch', { name: 'Chỉ mã đang dùng trong định mức' })).not.toBeChecked()
    expect(screen.getByRole('switch', { name: 'Hiện số lượng' })).not.toBeChecked()
    await user.click(screen.getByRole('switch', { name: 'Hiện số lượng' }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, showQty: true })
    await user.click(screen.getByRole('switch', { name: 'Chỉ mã đã có giá' }))
    expect(onChange).toHaveBeenLastCalledWith({ ...FILTERS, onlyPriced: true })
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
