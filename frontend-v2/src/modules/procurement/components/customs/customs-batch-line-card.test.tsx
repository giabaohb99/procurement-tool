import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { CustomsBatchLineCard } from './customs-batch-line-card'

describe('CustomsBatchLineCard', () => {
  it('shows row number, outcome badge, product name and the full message', () => {
    render(
      <CustomsBatchLineCard
        rowNo={12}
        badge={<span>Đã có</span>}
        productName="ATRAZINE 97% TECH"
        message="Đã có trong bảng giá (lô #3) — bỏ qua"
      />,
    )

    expect(screen.getByText('Dòng 12')).toBeInTheDocument()
    expect(screen.getByText('Đã có')).toBeInTheDocument()
    expect(screen.getByText('ATRAZINE 97% TECH')).toBeInTheDocument()
    expect(screen.getByText('Đã có trong bảng giá (lô #3) — bỏ qua')).toBeInTheDocument()
  })

  it('a batch-level note (no row) says so instead of "Dòng 0" or "Dòng null"', () => {
    const { rerender, container } = render(
      <CustomsBatchLineCard rowNo={null} badge={<span>Lỗi</span>} message="Không đọc được sheet" />,
    )
    expect(screen.getByText('Không gắn dòng')).toBeInTheDocument()
    expect(container.textContent).not.toMatch(/null/)

    rerender(<CustomsBatchLineCard rowNo={0} badge={<span>Lỗi</span>} message="x" />)
    expect(screen.queryByText('Dòng 0')).toBeNull()
  })

  it('an error row without a product name does not print an empty heading or a dash', () => {
    render(<CustomsBatchLineCard rowNo={3} badge={<span>Lỗi</span>} productName="" message="Thiếu ngày" />)

    expect(screen.queryByText('—')).toBeNull()
    expect(screen.getByText('Thiếu ngày')).toBeInTheDocument()
  })
})
