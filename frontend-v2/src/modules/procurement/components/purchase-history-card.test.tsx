import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { PurchaseHistoryRow } from '../api/purchase-request-support-api'
import { PurchaseHistoryCard } from './purchase-history-card'

function history(overrides: Partial<PurchaseHistoryRow> = {}): PurchaseHistoryRow {
  return {
    id: 7,
    po_id: 70,
    po_code: 'PO-2026-070',
    source: 'po',
    product_code: 'VTBB-01',
    product_name: 'Thùng carton',
    supplier_code: 'NCC-B',
    supplier_name: 'CÔNG TY B',
    company_id: 1,
    company_name: 'DEGO HOLDING',
    order_date: '2026-08-15',
    unit: 'Thùng',
    qty_order: 1_200,
    price: 8_750.25,
    vat: 8,
    amount: 10_500_300,
    completed_at: '2026-08-20',
    extra: {},
    invoice_name: 'Thùng carton 5 lớp',
    invoice_name_from_catalog: false,
    ...overrides,
  }
}

describe('PurchaseHistoryCard', () => {
  it('shows supplier, PO code, date, company, unit price, qty, VAT and full amount', () => {
    render(<PurchaseHistoryCard row={history()} readOnly={false} onPick={() => {}} />)

    expect(screen.getByText('CÔNG TY B')).toBeInTheDocument()
    expect(screen.getByText('PO-2026-070')).toBeInTheDocument()
    expect(screen.getByText(/15\/08\/2026/)).toBeInTheDocument()
    expect(screen.getByText(/DEGO HOLDING/)).toBeInTheDocument()
    expect(screen.getByText('8.750,25/Thùng')).toBeInTheDocument()
    expect(screen.getByText('SL 1.200')).toBeInTheDocument()
    expect(screen.getByText('VAT 8%')).toBeInTheDocument()
    expect(screen.getByText('10.500.300')).toBeInTheDocument()
  })

  it('picks the price only through the explicit button', () => {
    const onPick = vi.fn()
    render(<PurchaseHistoryCard row={history()} readOnly={false} onPick={onPick} />)

    //  Chạm vào chữ để đọc không được điền giá — chỉ nút mới điền.
    fireEvent.click(screen.getByText('CÔNG TY B'))
    expect(onPick).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: 'Dùng giá này' }))
    expect(onPick).toHaveBeenCalledTimes(1)
  })

  it('read-only (locked document) shows the old price but offers no way to fill it in', () => {
    render(<PurchaseHistoryCard row={history()} readOnly onPick={() => {}} />)

    expect(screen.getByText('8.750,25/Thùng')).toBeInTheDocument()
    expect(screen.queryByRole('button')).toBeNull()
  })

  it('legacy rows without a PO code say so instead of leaving the slot empty', () => {
    render(<PurchaseHistoryCard row={history({ po_code: '' })} readOnly onPick={() => {}} />)

    expect(screen.getByText('Dữ liệu cũ')).toBeInTheDocument()
  })

  it('invoice name taken from the catalog is marked with the explanatory title', () => {
    render(
      <PurchaseHistoryCard
        row={history({ invoice_name_from_catalog: true })}
        readOnly
        onPick={() => {}}
      />,
    )

    expect(screen.getByText('Thùng carton 5 lớp')).toHaveAttribute(
      'title',
      'Dữ liệu cũ không có — lấy theo danh mục sản phẩm',
    )
  })

  it('no invoice name at all drops the line instead of printing a bare label', () => {
    render(<PurchaseHistoryCard row={history({ invoice_name: '' })} readOnly onPick={() => {}} />)

    expect(screen.queryByText(/Tên HĐ/)).toBeNull()
  })

  it('never appends "đ" — imported orders store the price in foreign currency', () => {
    //  Lỗi rà mã duoc-CR-720 (N1): `price` chép thẳng từ dòng ĐMH, ĐMH nhập khẩu lưu
    //  nguyên tệ, nên gắn "đ" là 2,8 USD/kg hiện thành "2,8 đ/kg". Dòng lịch sử không
    //  khai tiền tệ thì thẻ in số trơn, đúng như bảng khổ rộng.
    const { container } = render(
      <PurchaseHistoryCard
        row={history({ price: 2.8, unit: 'kg', qty_order: 500, amount: 1_400 })}
        readOnly={false}
        onPick={() => {}}
      />,
    )

    expect(screen.getByText('2,8/kg')).toBeInTheDocument()
    expect(screen.getByText('1.400')).toBeInTheDocument()
    expect(container.textContent).not.toMatch(/\d\s*đ/)
  })
})
