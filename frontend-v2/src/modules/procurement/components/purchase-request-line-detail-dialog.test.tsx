import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { PurchaseRequestItem } from '../types/purchase-request-detail'
import { PurchaseRequestLineDetailDialog } from './purchase-request-line-detail-dialog'

// Popup này chỉ nói về CÁCH HIỆN dữ liệu dòng; hai khối ảnh gọi mạng nên cắt đi.
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestAttachments: () => ({ data: [], isLoading: false }),
  useUploadPurchaseRequestAttachments: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeletePurchaseRequestAttachment: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

const ITEM: PurchaseRequestItem = {
  id: 7,
  product_code: '01RR0035V3-170426',
  product_name: 'Nhãn decal cuộn - khổ 50mm',
  item_group: 'Băng keo',
  group_desc: '',
  qty: 2000,
  unit: 'Cái',
  price: 1200,
  vat_pct: 0,
  amount: 2400000,
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
}

function renderDialog(
  props: Partial<Parameters<typeof PurchaseRequestLineDetailDialog>[0]> = {},
) {
  render(
    <PurchaseRequestLineDetailDialog
      item={ITEM}
      lineNumber={1}
      open
      editing={false}
      showAssignee={false}
      canEditProgress={false}
      canAssign={false}
      canManageAttachments={false}
      onOpenChange={vi.fn()}
      onChange={vi.fn()}
      onSaveOperational={vi.fn(async () => {})}
      {...props}
    />,
  )
}

describe('PurchaseRequestLineDetailDialog', () => {
  /**
   * Lỗi đã gặp: mọi ô đều là `<Input disabled>` nên người dùng KHÔNG bôi đen và
   * KHÔNG copy được mã vật tư ra ngoài, lại còn bị làm mờ 50% nhìn như ô trống.
   */
  it('phiếu chỉ xem thì giá trị hiện dạng chữ copy được, không phải ô nhập bị khóa', () => {
    renderDialog()

    expect(screen.getByText('01RR0035V3-170426')).toBeInTheDocument()
    expect(screen.getByText('Nhãn decal cuộn - khổ 50mm')).toBeInTheDocument()
    // Không còn ô nhập nào giữ giá trị này -> chữ nằm ngoài input, bôi đen được.
    expect(screen.queryByDisplayValue('01RR0035V3-170426')).toBeNull()
    expect(document.querySelectorAll('input:disabled, textarea:disabled')).toHaveLength(0)
  })

  it('số lượng và đơn giá chỉ xem thì có ngăn cách hàng nghìn cho dễ đọc', () => {
    renderDialog()

    expect(screen.getByText('2.000')).toBeInTheDocument()
    expect(screen.getByText('1.200')).toBeInTheDocument()
  })

  it('đang sửa thì vẫn là ô nhập gõ được như cũ', () => {
    renderDialog({ editing: true })

    expect(screen.getByDisplayValue('01RR0035V3-170426')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Nhãn decal cuộn - khổ 50mm')).toBeInTheDocument()
  })

  /**
   * Lỗi đã gặp: phiếu nháp mở popup ra thấy toàn chữ chết, người dùng đọc thành
   * "hết quyền sửa" vì nút Sửa duy nhất nằm tận thanh công cụ đầu trang.
   */
  it('phiếu còn sửa được mà đang xem thì popup mời bật chế độ sửa', async () => {
    const onStartEditing = vi.fn()
    renderDialog({ documentEditable: true, onStartEditing })

    await userEvent.click(screen.getByRole('button', { name: /Sửa dòng này/ }))

    expect(onStartEditing).toHaveBeenCalledTimes(1)
  })

  it('đang sửa rồi thì thôi mời sửa nữa', () => {
    renderDialog({ editing: true, documentEditable: true, onStartEditing: vi.fn() })

    expect(screen.queryByRole('button', { name: /Sửa dòng này/ })).toBeNull()
  })
})
