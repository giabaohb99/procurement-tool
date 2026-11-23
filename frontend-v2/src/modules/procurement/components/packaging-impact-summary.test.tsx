import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { PackagingImpactKpis } from '../types/packaging-cost-types'
import { PackagingImpactSummary } from './packaging-impact-summary'

const kpis: PackagingImpactKpis = {
  selected_count: 3,
  selected_by_group: { Chai: 2, Nắp: 1 },
  assumed_count: 1,
  affected_products: 284,
  increased: 12,
  decreased: 0,
  max_increase_carton: 20000,
  max_increase_bottle: 500,
  max_increase_product: {
    hh_code: 'HH0417.1',
    hh_name: 'Nước tương Dego chai 450ml thùng 40 chai',
    diff_bottle: 500,
    diff_carton: 20000,
    carton_qty: 40,
  },
}

describe('PackagingImpactSummary', () => {
  it('shows the selected and affected counts as cards, not a text line', () => {
    render(<PackagingImpactSummary kpis={kpis} onShowTopIncrease={vi.fn()} />)
    expect(screen.getByText('Mã đã chọn')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('2 chai · 1 nắp · 1 mã giả định')).toBeInTheDocument()
    expect(screen.getByText('Sản phẩm bị ảnh hưởng')).toBeInTheDocument()
    expect(screen.getByText('284')).toBeInTheDocument()
    expect(screen.getByText('Dùng ít nhất 1 mã đã chọn')).toBeInTheDocument()
    //  Chỉ ba thẻ: không đưa lại thẻ "Sản phẩm tăng chi phí" (người chủ đã bỏ).
    expect(screen.queryByText(/Sản phẩm tăng chi phí/)).not.toBeInTheDocument()
  })

  it('highlights the product with the biggest per-carton rise and its per-bottle rise', () => {
    render(<PackagingImpactSummary kpis={kpis} onShowTopIncrease={vi.fn()} />)
    expect(screen.getByText('Tăng nhiều nhất /thùng')).toBeInTheDocument()
    const value = screen.getByText('+20.000')
    expect(value).toHaveClass('text-emerald-600')          // chi phí tăng = xanh
    expect(screen.getByText('VNĐ/thùng')).toBeInTheDocument()
    expect(screen.getByText('+500 /chai')).toBeInTheDocument()
    const detail = screen.getByText(/HH0417\.1 — Nước tương Dego/)
    expect(detail).toHaveAttribute('title', 'HH0417.1 — Nước tương Dego chai 450ml thùng 40 chai')   // dài thì cắt, rê chuột xem đủ
  })

  it('clicking the highlighted card asks the page to sort by per-carton rise', () => {
    const onShow = vi.fn()
    render(<PackagingImpactSummary kpis={kpis} onShowTopIncrease={onShow} />)
    fireEvent.click(screen.getByRole('button', { name: /Tăng nhiều nhất \/thùng/ }))
    expect(onShow).toHaveBeenCalledTimes(1)
  })

  it('says "no product rises" instead of a number, and the card is not clickable', () => {
    const onShow = vi.fn()
    render(
      <PackagingImpactSummary
        kpis={{ ...kpis, max_increase_carton: -4000, max_increase_product: null }}
        onShowTopIncrease={onShow}
      />,
    )
    expect(screen.getByText('Không có sản phẩm tăng')).toBeInTheDocument()
    expect(screen.queryByText(/-4\.000|4\.000/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('names the filtered count against the unfiltered total only while filtering', () => {
    const { rerender } = render(<PackagingImpactSummary kpis={kpis} filteredTotal={12} onShowTopIncrease={vi.fn()} />)
    expect(screen.getByText('Đang lọc: 12 / 284')).toBeInTheDocument()
    expect(screen.queryByText('Dùng ít nhất 1 mã đã chọn')).not.toBeInTheDocument()
    rerender(<PackagingImpactSummary kpis={kpis} filteredTotal={0} onShowTopIncrease={vi.fn()} />)
    expect(screen.getByText('Đang lọc: 0 / 284')).toBeInTheDocument()   // lọc ra 0 vẫn là đang lọc
  })

  it('renders nothing before the first answer arrives', () => {
    const { container } = render(<PackagingImpactSummary kpis={undefined} onShowTopIncrease={vi.fn()} />)
    expect(container).toBeEmptyDOMElement()
  })
})
