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
    line_status: 'no_po',
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
   * QA 29/08: nút "Sửa dòng hàng" đã BỎ — phiếu còn sửa được thì trang mở thẳng
   * chế độ sửa như v1, bảng chỉ còn hai trạng thái xem / nhập trực tiếp.
   */
  it('không còn nút Sửa dòng hàng — bảng xem là xem, nhập là nhập', () => {
    const { unmount } = renderTable({ editing: false })
    expect(screen.queryByRole('button', { name: /Sửa dòng hàng/ })).toBeNull()
    unmount()

    renderTable({ editing: true })
    expect(screen.getByRole('button', { name: /Thêm dòng/ })).toBeInTheDocument()
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

/**
 * Khổ điện thoại — bảng đổi sang THẺ, xem `PurchaseRequestLineCard`.
 *
 * Khách báo 14/09/2026: bảng 15–16 cột rộng ~2000px nằm trong khung 322px, phần
 * nhìn thấy được là *No. · Mã hàng* và một mẩu tên hàng — số lượng, thành tiền và
 * trạng thái dòng đều ngoài mép phải, mà thanh cuộn ngang thì iOS ẩn sẵn. Người
 * dùng đọc ra là "chữ bị lỗi" chứ không phải "vuốt sang đi".
 *
 * `setup.ts` cố định `matchMedia` ở khổ desktop cho cả bộ test, nên khổ hẹp phải
 * nói rõ ra ngay tại đây.
 */
describe('PurchaseRequestItemsTable — khổ điện thoại', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal('matchMedia', (query: string) => ({
      matches: true,
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it('bày SỐ LƯỢNG và THÀNH TIỀN của dòng — hai cột nằm ngoài mép phải của bảng', () => {
    renderTable()

    // Số tiền của dòng: `amount` = 972.000 (phiếu đã lưu thì lấy cột backend).
    expect(screen.getByText(/972\.000 đ/)).toBeInTheDocument()
    // SL × đơn giá đứng cùng một mẩu chữ, nên khẳng định theo cả cụm.
    expect(screen.getByText(/1\.000 Cái × 900/)).toBeInTheDocument()
    // Dòng mẫu ở `line_status: 'no_po'` — nhãn tra từ `PR_LINE_STATUS`.
    expect(screen.getByText(/Chưa tạo đơn mua hàng/)).toBeInTheDocument()
  })

  it('KHÔNG bày cụm điều khiển cột — ở chế độ thẻ chúng không điều khiển thứ gì', () => {
    renderTable()

    expect(screen.queryByRole('button', { name: /Cột/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Bảng rút gọn|Bảng đầy đủ/ })).toBeNull()
  })

  it('cả thẻ là một nút mở hộp chi tiết — mọi ô vẫn sửa được ở đó', async () => {
    const onOpenDetail = vi.fn()
    renderTable({ onOpenDetail })

    await userEvent.click(screen.getByRole('button', { name: /Nắp nhựa phi 28/ }))
    expect(onOpenDetail).toHaveBeenCalledWith(0)
  })
})
