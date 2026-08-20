import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { PurchaseRequestItem } from '../types/purchase-request-detail'
import { PurchaseRequestItemsTable } from './purchase-request-items-table'

// Bảng này nói về CÁCH HIỆN dòng hàng, không nói về mạng — cắt hết lượt gọi
// danh mục (kho / ĐVT / phân loại / sản phẩm / lịch sử mua hàng).
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestWarehouses: () => ({ data: { items: [] }, isLoading: false }),
  usePurchaseRequestUnits: () => ({ data: { items: [] }, isLoading: false }),
  usePurchaseRequestItemGroups: () => ({ data: { items: [] }, isLoading: false }),
  usePurchaseRequestProducts: () => ({ data: { items: [] }, isLoading: false }),
  useProductPurchaseHistory: () => ({
    data: { total: 0, items: [] },
    isLoading: false,
    isError: false,
    isFetching: false,
  }),
}))

const ITEMS: PurchaseRequestItem[] = [
  {
    id: 7,
    product_code: 'NAP0029',
    product_name: 'Nắp nhựa phi 28',
    item_group: 'Bao bì',
    group_desc: '',
    qty: 1000,
    unit: 'Cái',
    price: 900,
    vat_pct: 8,
    amount: 972000,
    warehouse: 'Kho HCM',
    required_date: '2026-05-20',
    assignee: '',
    expected_date: '',
    line_status: 'Chưa đặt hàng',
    progress_note: '',
    note: '',
    qty_ordered: 0,
    qty_received: 0,
    product_id: 3,
    product_thumbnail_url: '',
  },
]

function renderTable(
  props: Partial<Parameters<typeof PurchaseRequestItemsTable>[0]> = {},
) {
  return render(
    <PurchaseRequestItemsTable
      items={ITEMS}
      editing={false}
      onChange={vi.fn()}
      onOpenDetail={vi.fn()}
      {...props}
    />,
  )
}

describe('PurchaseRequestItemsTable', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  /**
   * Lỗi đã gặp: phiếu nháp mở ra ở chế độ XEM, nút "Sửa" duy nhất lại nằm tít
   * trên đầu trang lẫn giữa gần chục nút khác, nên người dùng (kể cả admin)
   * tưởng mình không có quyền thêm dòng / sửa dòng.
   */
  it('phiếu còn sửa được mà đang xem thì có lối vào chế độ sửa ngay cạnh bảng', async () => {
    const onStartEditing = vi.fn()
    renderTable({ documentEditable: true, onStartEditing })

    await userEvent.click(screen.getByRole('button', { name: /Sửa dòng hàng/ }))

    expect(onStartEditing).toHaveBeenCalledTimes(1)
  })

  it('phiếu đã chốt thì không mời gọi sửa dòng nữa', () => {
    renderTable({ documentEditable: false, onStartEditing: vi.fn() })

    expect(screen.queryByRole('button', { name: /Sửa dòng hàng/ })).toBeNull()
  })

  /**
   * Lỗi đã gặp: lúc sửa, mã hàng nằm trong ô CHỌN (một `<button>`) nên bôi đen
   * không được — không ai chép nổi mã đem đi tra ở nơi khác.
   */
  it('mã hàng luôn có nút chép, kể cả khi đang sửa', () => {
    const { unmount } = renderTable({ editing: true })
    expect(screen.getByRole('button', { name: /Chép mã hàng/ })).toBeInTheDocument()
    unmount()

    renderTable({ editing: false })
    expect(screen.getByRole('button', { name: /Chép mã hàng/ })).toBeInTheDocument()
  })
})
