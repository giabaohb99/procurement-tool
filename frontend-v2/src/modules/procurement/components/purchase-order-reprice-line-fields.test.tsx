import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import { PurchaseOrderRepriceLineFields } from './purchase-order-reprice-line-fields'

const saved = { id: 7, qty_order: 220, price: 69_444.44, vat: 8 } as PurchaseOrderItem

describe('PurchaseOrderRepriceLineFields', () => {
  it('shows only the lock reason when the server blocks the line', () => {
    render(
      <PurchaseOrderRepriceLineFields
        item={saved}
        original={saved}
        lockReason="Dòng đã nằm trên YCTT PR00012 (đang chờ duyệt) — trả phiếu đó về trước"
        importMode={false}
        onChange={vi.fn()}
      />,
    )
    expect(screen.getByText(/YCTT PR00012/)).toBeInTheDocument()
    expect(screen.queryByLabelText('Đơn giá')).not.toBeInTheDocument()
  })

  it('shows the saved value under a field that was changed', () => {
    render(
      <PurchaseOrderRepriceLineFields
        item={{ ...saved, price: 70_000 }}
        original={saved}
        lockReason=""
        importMode={false}
        onChange={vi.fn()}
      />,
    )
    expect(screen.getAllByText(/Đang lưu:/).length).toBeGreaterThan(0)
    expect(screen.getByText('69.444,44')).toBeInTheDocument()
  })

  it('hides both VAT fields on an import order', () => {
    render(
      <PurchaseOrderRepriceLineFields
        item={saved}
        original={saved}
        lockReason=""
        importMode
        onChange={vi.fn()}
      />,
    )
    expect(screen.getByLabelText('Đơn giá')).toBeInTheDocument()
    expect(screen.queryByLabelText('Đơn giá (Sau VAT)')).not.toBeInTheDocument()
  })

  //  Người chủ chốt 20/11/2026: bấm Sửa giá là con trỏ phải nằm ngay ô giá, không bắt người dùng đi tìm.
  it('puts the cursor in the unit price box once the line is confirmed editable', () => {
    const { rerender } = render(
      <PurchaseOrderRepriceLineFields
        item={saved}
        original={saved}
        lockReason="Đang kiểm tra dòng này có sửa giá được không…"
        importMode={false}
        onChange={vi.fn()}
      />,
    )
    expect(document.body).toHaveFocus()
    rerender(
      <PurchaseOrderRepriceLineFields
        item={saved}
        original={saved}
        lockReason=""
        importMode={false}
        onChange={vi.fn()}
      />,
    )
    expect(screen.getByLabelText('Đơn giá')).toHaveFocus()
  })
})
