import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { ShippingDetailRow } from '../types/purchase-report'
import { ReportShippingDetailCard } from './report-shipping-detail-card'

function shipping(overrides: Partial<ShippingDetailRow> = {}): ShippingDetailRow {
  return {
    carrier: 'Vận tải Minh Phát',
    month: '2026-08',
    product_code: 'VTBB-01',
    misa_code: 'MS-123',
    invoice_no: '0001234',
    received_date: '2026-08-20',
    qty_order: 1_000,
    qty_received: 950,
    order_amount: 25_000_000,
    ship_amount: 1_250_000,
    rate: 5,
    ...overrides,
  }
}

describe('ReportShippingDetailCard', () => {
  it('leads with the carrier and keeps every column of the table on the card', () => {
    render(<ReportShippingDetailCard row={shipping()} />)

    expect(screen.getByText('Vận tải Minh Phát')).toBeInTheDocument()
    expect(screen.getByText('VTBB-01')).toBeInTheDocument()
    expect(screen.getByText(/2026-08/)).toBeInTheDocument()
    expect(screen.getByText(/MISA MS-123/)).toBeInTheDocument()
    expect(screen.getByText(/HĐ 0001234/)).toBeInTheDocument()
    expect(screen.getByText(/Nhận 20\/08\/2026/)).toBeInTheDocument()
    expect(screen.getByText(/SL đặt 1\.000 · nhận 950/)).toBeInTheDocument()
    //  Tiền in đủ chữ số, không rút gọn kiểu "25 tr".
    expect(screen.getByText('25.000.000 đ')).toBeInTheDocument()
    expect(screen.getByText('1.250.000 đ')).toBeInTheDocument()
    expect(screen.getByText('5%')).toBeInTheDocument()
  })

  it('empty invoice and received date drop that line instead of printing a lone dot', () => {
    render(<ReportShippingDetailCard row={shipping({ invoice_no: '', received_date: '' })} />)

    expect(screen.queryByText(/HĐ/)).toBeNull()
    expect(screen.queryByText(/Nhận/)).toBeNull()
  })

  it('a zero rate still prints "0%" — zero shipping cost is a real figure', () => {
    render(<ReportShippingDetailCard row={shipping({ ship_amount: 0, rate: 0 })} />)

    expect(screen.getByText('0%')).toBeInTheDocument()
    expect(screen.getByText('0 đ')).toBeInTheDocument()
  })

  it('missing carrier and product code show dashes, not blank lines', () => {
    render(<ReportShippingDetailCard row={shipping({ carrier: '', product_code: '' })} />)

    expect(screen.getAllByText('—')).toHaveLength(2)
  })
})
