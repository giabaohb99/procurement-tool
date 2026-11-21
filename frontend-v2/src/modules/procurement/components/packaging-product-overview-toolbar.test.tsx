import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { PackagingProductOverviewToolbar } from './packaging-product-overview-toolbar'

const COUNTS = { all: 6, up: 2, down: 1, flat: 2, missing: 1 }

function setup(over: Partial<Parameters<typeof PackagingProductOverviewToolbar>[0]> = {}) {
  const onKeywordChange = vi.fn()
  const onTrendChange = vi.fn()
  render(
    <PackagingProductOverviewToolbar
      keyword=""
      onKeywordChange={onKeywordChange}
      trend="all"
      onTrendChange={onTrendChange}
      counts={COUNTS}
      {...over}
    />,
  )
  return { onKeywordChange, onTrendChange, user: userEvent.setup() }
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
})
