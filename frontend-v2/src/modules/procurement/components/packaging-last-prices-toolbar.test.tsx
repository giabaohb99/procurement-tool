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
  it('shows one multi-select box for groups, "Tất cả" first in its list and not ticked until chosen', async () => {
    const { user } = setup()
    expect(screen.queryByRole('button', { name: /^Chai/ })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /Nhóm sản phẩm/ }))
    //  Mỗi nhóm một dòng tick, số mã là chữ phụ; dòng đầu là "Tất cả", không có hàng "Chọn tất cả" của ô chọn.
    const rows = screen.getAllByRole('button', { name: /^(Tất cả|Chai\s*12|Nắp\s*3)$/ })
    expect(rows.map((row) => row.textContent?.replace(/\d+$/, '').trim())).toEqual(['Tất cả', 'Chai', 'Nắp'])
    expect(screen.queryByRole('button', { name: /Chọn tất cả/ })).not.toBeInTheDocument()
  })

  it('ticks a group by its exact name (not the label with the count)', async () => {
    const { onChange, user } = setup()
    await user.click(screen.getByRole('button', { name: /Nhóm sản phẩm/ }))
    await user.click(screen.getByRole('button', { name: /^Nắp\s*3$/ }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, groups: ['Nắp'], all: false })
  })

  it('"Tất cả" in the list clears the chosen groups and loads everything', async () => {
    const { onChange, user } = setup({ ...FILTERS, groups: ['Nắp'] })
    await user.click(screen.getByRole('button', { name: /^Nắp$/ }))
    await user.click(screen.getByRole('button', { name: /^Tất cả$/ }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, groups: [], all: true })
  })

  it('names "Tất cả" in the box when all is on; ticking a group then leaves "Tất cả"', async () => {
    const { onChange, user } = setup({ ...FILTERS, all: true })
    await user.click(screen.getByRole('button', { name: /^Tất cả$/ }))
    await user.click(screen.getByRole('button', { name: /^Chai\s*12$/ }))
    expect(onChange).toHaveBeenCalledWith({ ...FILTERS, groups: ['Chai'], all: false })
  })

  it('shows the recent-mode caption only in recent mode', () => {
    const { rerender } = render(
      <PackagingLastPricesToolbar filters={{ ...FILTERS, all: true }} groups={GROUPS} suppliers={SUPPLIERS} onChange={vi.fn()} />,
    )
    expect(screen.queryByText(/mã mua gần nhất/)).not.toBeInTheDocument()
    rerender(
      <PackagingLastPricesToolbar filters={FILTERS} groups={GROUPS} suppliers={SUPPLIERS} onChange={vi.fn()} recentMode />,
    )
    expect(screen.getByText('20 mã mua gần nhất · chọn Tất cả ở ô Nhóm sản phẩm để xem hết')).toBeInTheDocument()
  })

  it('names the chosen groups in the box, appends in tick order and unticking one removes it', async () => {
    const { onChange, user } = setup({ ...FILTERS, groups: ['Nắp'] })
    await user.click(screen.getByRole('button', { name: /^Nắp$/ }))
    await user.click(screen.getByRole('button', { name: /^Chai\s*12$/ }))
    expect(onChange).toHaveBeenLastCalledWith({ ...FILTERS, groups: ['Nắp', 'Chai'], all: false })
    await user.click(screen.getByRole('button', { name: /^Nắp\s*3$/ }))
    expect(onChange).toHaveBeenLastCalledWith({ ...FILTERS, groups: [], all: false })
  })

  it('keeps a chosen group listed (count 0) when the server no longer lists it, so it can be unticked', async () => {
    const { onChange, user } = setup({ ...FILTERS, groups: ['Nhãn'] })
    await user.click(screen.getByRole('button', { name: /^Nhãn$/ }))
    await user.click(screen.getByRole('button', { name: /^Nhãn\s*0$/ }))
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
