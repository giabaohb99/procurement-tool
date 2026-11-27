import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { PackagingPriceRow } from '../types/packaging-cost-types'
import { PackagingPriceRowCard } from './packaging-price-row-card'

//  bao-CR-792: mã / số chứng từ chỉ thành đường bấm khi có quyền ở màn đích — bài kiểm này đứng ở vai người có đủ quyền.
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true }),
}))

const row: PackagingPriceRow = {
  code: 'CET0028',
  name: 'Chai PAPE tròn cổ 43',
  group: 'Chai',
  unit: 'Cái',
  purchase_count: 3,
  last_date: '2026-06-30',
  last_purchase_price: 3170,
  last_purchase_date: '2026-06-30',
  prev_purchase_price: 4300,
  quote: { price: 3500.5, valid_from: '2026-11-20' },
  old: 3170,
  new: 3500.5,
  diff: 330.5,
  pct: 0.104,
  usage: 30,
  min: 3170,
  max: 4724,
  warnings: [],
}

describe('PackagingPriceRowCard', () => {
  it('shows the price-list fields under the table headers', () => {
    render(
      <MemoryRouter>
        <PackagingPriceRowCard row={row} />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'CET0028' })).toBeInTheDocument()
    for (const label of ['Số lần mua', 'Mua gần nhất', 'Giá mua gần nhất', 'Giá mua lần trước', 'Báo giá mới', 'Số SP đang dùng', 'Tiền tệ']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
    expect(screen.getByText('VND')).toBeInTheDocument()
    expect(screen.getByText('30/06/2026')).toBeInTheDocument()
    expect(screen.getByText('20/11/2026')).toBeInTheDocument()
    expect(screen.getByText('+330,5')).toHaveClass('text-destructive')
    expect(screen.queryByRole('button', { name: 'Báo giá' })).not.toBeInTheDocument()
  })

  //  bao-CR-800 — thẻ của Bảng giá nguyên liệu: màn Lịch sử mua hàng của cụm không còn mã nguyên liệu nên mã KHÔNG được là
  //  đường bấm (kể cả người có đủ quyền), và nguyên liệu không nằm trong định mức nên không có dòng Số SP đang dùng.
  //  bao-CR-801 — mã nguyên liệu mở màn Lịch sử mua NGUYÊN LIỆU (không phải Lịch sử mua hàng của VTBB).
  it('renders a raw-material row with a code linking to the material history and without the usage field', () => {
    render(
      <MemoryRouter>
        <PackagingPriceRowCard row={{ ...row, code: 'NL0001', usage: 0 }} rawMaterial />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'NL0001' })).toHaveAttribute(
      'href',
      '/procurement/packaging-cost/material-history?codes=NL0001',
    )
    expect(screen.queryByText('Số SP đang dùng')).not.toBeInTheDocument()
    for (const label of ['Số lần mua', 'Giá mua gần nhất', 'Báo giá mới', 'Min', 'Max', 'Tiền tệ']) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
    expect(screen.queryByRole('button', { name: 'Báo giá' })).not.toBeInTheDocument()
  })

  it('opens a new quote for the code when the user may quote', () => {
    const onQuote = vi.fn()
    render(
      <MemoryRouter>
        <PackagingPriceRowCard row={row} onQuote={onQuote} />
      </MemoryRouter>,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Báo giá' }))
    expect(onQuote).toHaveBeenCalledWith(row)
  })
})
