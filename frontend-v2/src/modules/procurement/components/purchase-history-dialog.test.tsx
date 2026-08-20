import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { PurchaseHistoryDialog } from './purchase-history-dialog'

// Màn này chỉ nói về CÁCH HIỆN lịch sử mua hàng, không nói về mạng — thay lượt
// gọi API bằng đúng một dòng dữ liệu tĩnh.
vi.mock('../hooks/use-purchase-request-support', () => ({
  useProductPurchaseHistory: () => ({
    data: {
      total: 1,
      items: [
        {
          id: 11,
          po_id: 352,
          po_code: 'PO-2026-001',
          source: 'po',
          product_code: 'SP-001',
          product_name: 'Thùng carton',
          supplier_code: 'NCC-A',
          supplier_name: 'CÔNG TY A',
          company_id: 1,
          company_name: 'DEGO',
          order_date: '2026-05-04',
          unit: 'Cái',
          qty_order: 100,
          price: 12000,
          vat: 8,
          amount: 1296000,
          completed_at: '2026-05-20',
          extra: {},
        },
      ],
    },
    isLoading: false,
    isError: false,
    isFetching: false,
  }),
}))

function renderDialog(props: Partial<Parameters<typeof PurchaseHistoryDialog>[0]> = {}) {
  const onPick = vi.fn()
  const onOpenChange = vi.fn()
  render(
    <PurchaseHistoryDialog
      open
      productCode="SP-001"
      productName="Thùng carton"
      onOpenChange={onOpenChange}
      onPick={onPick}
      {...props}
    />,
  )
  return { onPick, onOpenChange }
}

describe('PurchaseHistoryDialog', () => {
  it('phiếu đang sửa thì chọn được một lần mua cũ để điền giá', async () => {
    const user = userEvent.setup()
    const { onPick, onOpenChange } = renderDialog()

    await user.click(screen.getByRole('button', { name: 'Dùng giá này' }))

    expect(onPick).toHaveBeenCalledWith(expect.objectContaining({ id: 11, price: 12000 }))
    // Chọn xong là đóng luôn, không bắt bấm thêm nút Đóng.
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  /**
   * Đơn đang chờ duyệt bị khóa sửa, nhưng đó chính là lúc người duyệt cần đối
   * chiếu giá cũ — nên vẫn phải XEM được, chỉ bỏ đường điền giá đi.
   */
  it('chỉ xem thì vẫn thấy giá cũ nhưng không có đường điền vào phiếu', async () => {
    const user = userEvent.setup()
    const { onPick } = renderDialog({ readOnly: true })

    expect(screen.getByText('PO-2026-001')).toBeInTheDocument()
    expect(screen.queryByRole('columnheader', { name: 'Chọn' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Dùng giá này' })).toBeNull()
    expect(screen.getByText(/Chỉ xem để tham khảo/)).toBeInTheDocument()

    // Bấm cả dòng cũng không được điền — v1 để dòng bấm được nên hay lỡ tay.
    await user.click(screen.getByText('PO-2026-001'))
    expect(onPick).not.toHaveBeenCalled()
  })
})
