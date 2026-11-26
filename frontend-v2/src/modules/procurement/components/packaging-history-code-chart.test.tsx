// duoc-CR-784 — biểu đồ giá theo thành phần (Lịch sử mua hàng, chế độ một sản phẩm): chú giải = vai trò + mã cho MỌI đường, và bản in
// vẽ đúng một đường (path) cho mỗi mã có lần mua. Biểu đồ màn hình dùng recharts nên jsdom (khung rộng 0) chỉ kiểm được chú giải + tiêu đề.
import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { PackagingHistorySeriesLine } from '../types/packaging-cost-types'
import { PackagingHistoryCodeChart } from './packaging-history-code-chart'
import { PrintCodeChart } from './packaging-history-print-code-chart'

const lines: PackagingHistorySeriesLine[] = [
  { code: 'CPT0105', name: 'Chai 450ml', role: 1, points: [{ date: '2026-01-01', price: 100 }, { date: '2026-02-01', price: 110 }] },
  { code: 'NAP0085', name: 'Nắp vặn', role: 2, points: [{ date: '2026-02-01', price: 200 }] },
  { code: 'THG0001', name: 'Thùng', role: 5, points: [{ date: '2026-03-01', price: 9000 }, { date: '2026-04-01', price: 9500 }] },
]

describe('PackagingHistoryCodeChart', () => {
  it('shows the title with the product and one legend entry per component code', () => {
    render(<PackagingHistoryCodeChart lines={lines} subject="HH0001 · Sản phẩm A" />)
    expect(screen.getByText(/Diễn biến đơn giá theo thành phần \(VNĐ\) — HH0001 · Sản phẩm A/)).toBeInTheDocument()
    const legend = screen.getByRole('list', { name: 'Chú giải' })
    expect(within(legend).getAllByRole('listitem').map((item) => item.textContent)).toEqual([
      'Chai · CPT0105',
      'Nắp · NAP0085',
      'Thùng · THG0001',
    ])
  })
})

describe('PrintCodeChart', () => {
  it('draws one path per code with its own colour and a legend of role + code', () => {
    const { container } = render(<PrintCodeChart lines={lines} />)
    expect(screen.getByRole('heading', { name: 'Diễn biến đơn giá theo thành phần (VNĐ)' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Diễn biến đơn giá theo thành phần' })).toBeInTheDocument()
    const paths = [...container.querySelectorAll('g[data-line] path')]
    expect(paths.map((path) => path.closest('g')?.getAttribute('data-line'))).toEqual(['CPT0105', 'NAP0085', 'THG0001'])
    expect(new Set(paths.map((path) => path.getAttribute('stroke'))).size).toBe(3)
    expect(paths[2]).toHaveAttribute('stroke-dasharray')                       // thùng = nét đứt
    expect(screen.getByText('Nắp · NAP0085')).toBeInTheDocument()
  })

  it('renders nothing without data', () => {
    const { container } = render(<PrintCodeChart lines={[]} />)
    expect(container).toBeEmptyDOMElement()
  })
})
