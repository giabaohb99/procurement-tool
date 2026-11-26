import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { EMPTY_IMPACT_FILTERS } from '../utils/packaging-impact-filters'
import { PackagingProductOverviewToolbar } from './packaging-product-overview-toolbar'

const COUNTS = { all: 6, up: 2, down: 1, flat: 2, missing: 1 }

function setup(over: Partial<Parameters<typeof PackagingProductOverviewToolbar>[0]> = {}) {
  const onKeywordChange = vi.fn()
  const onTrendChange = vi.fn()
  const onAdvancedChange = vi.fn()
  render(
    <PackagingProductOverviewToolbar
      keyword=""
      onKeywordChange={onKeywordChange}
      trend="all"
      onTrendChange={onTrendChange}
      counts={COUNTS}
      advanced={EMPTY_IMPACT_FILTERS}
      onAdvancedChange={onAdvancedChange}
      {...over}
    />,
  )
  return { onKeywordChange, onTrendChange, onAdvancedChange, user: userEvent.setup() }
}

describe('PackagingProductOverviewToolbar', () => {
  it('writes every count on its chip and marks only the active trend as pressed', () => {
    setup({ trend: 'down' })
    expect(screen.getByRole('button', { name: 'Tất cả (6)' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('button', { name: 'Giảm (1)' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Chưa có giá (1)' })).toBeInTheDocument()
  })

  it('shows plain labels until the first response gives the counts', () => {
    setup({ counts: undefined })
    expect(screen.getByRole('button', { name: 'Tăng' })).toBeInTheDocument()
  })

  it('reports the clicked trend and the typed keyword', async () => {
    const { onTrendChange, onKeywordChange, user } = setup()
    await user.click(screen.getByRole('button', { name: 'Không đổi (2)' }))
    expect(onTrendChange).toHaveBeenCalledWith('flat')
    await user.type(screen.getByLabelText('Tìm sản phẩm'), 'x')
    expect(onKeywordChange).toHaveBeenCalledWith('x')
  })

  it('keeps the trend count chips beside the add-condition button and applies a condition immediately', async () => {
    const { onAdvancedChange, user } = setup()
    expect(screen.getByRole('button', { name: 'Tất cả (6)' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /Thêm điều kiện/ }))
    expect(screen.queryByRole('menuitem', { name: 'Xu hướng chi phí' })).not.toBeInTheDocument()
    await user.click(screen.getByRole('menuitem', { name: 'Có mã ở vai trò' }))
    await user.click(await screen.findByRole('button', { name: 'Thùng' }))
    expect(onAdvancedChange).toHaveBeenCalledWith(expect.objectContaining({ roles: [5] }))
  })

  it('shows the chips of the filters already applied', () => {
    setup({ advanced: { ...EMPTY_IMPACT_FILTERS, pct: { min: '5', max: '' }, warningsOnly: true } })
    expect(screen.getByRole('button', { name: 'Sửa điều kiện: % chênh ≥ 5%' })).toBeInTheDocument()
    expect(screen.getByText('Chỉ SP có cảnh báo')).toBeInTheDocument()
  })
})
