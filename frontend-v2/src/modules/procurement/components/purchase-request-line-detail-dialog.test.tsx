import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PurchaseRequestItem } from '../types/purchase-request-detail'
import { PurchaseRequestLineDetailDialog } from './purchase-request-line-detail-dialog'

// Popup này chỉ nói về CÁCH HIỆN dữ liệu dòng; hai khối ảnh gọi mạng nên cắt đi. Ảnh trả về
// theo entity để từng bài tự bày ảnh gốc / ảnh đối chiếu (nút So sánh, hộp xóa ảnh).
const attachments = vi.hoisted(() => ({
  byEntity: {} as Record<string, unknown[]>,
  remove: vi.fn(async () => ({})),
}))
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestAttachments: (entity: string) => ({
    data: attachments.byEntity[entity] ?? [],
    isLoading: false,
  }),
  useUploadPurchaseRequestAttachments: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeletePurchaseRequestAttachment: () => ({ mutateAsync: attachments.remove, isPending: false }),
  //  Ô chọn mã VTBB (bao-CR-568) hiện khi NSTM sửa được tiến độ dòng chưa lên ĐMH.
  usePurchaseRequestProducts: () => ({ data: { items: [] }, isLoading: false }),
}))

function image(id: number, filename: string) {
  return { id, file_id: id, filename, url: `/files/${filename}`, content_type: 'image/jpeg', size: 1 }
}

beforeEach(() => {
  attachments.byEntity = {}
  attachments.remove.mockClear()
})

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
  line_status: 'no_po',
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

describe('PurchaseRequestLineDetailDialog — chữ và hành vi v1 (duoc-CR-741)', () => {
  it('the close button says "Đóng" while editing and "Hủy" otherwise, like v1', () => {
    renderDialog({ editing: true })
    expect(screen.getByRole('button', { name: 'Đóng' })).toBeInTheDocument()
  })

  it('a locked ticket closes with "Hủy"', () => {
    renderDialog({ editing: false })
    expect(screen.getByRole('button', { name: 'Hủy' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Đóng' })).toBeNull()
  })

  it('stays open when the page reports the save was abandoned (reason prompt cancelled)', async () => {
    const onOpenChange = vi.fn()
    renderDialog({
      canEditProgress: true,
      onOpenChange,
      onSaveOperational: vi.fn(async () => false),
    })

    await userEvent.click(screen.getByRole('button', { name: 'Lưu dòng' }))
    expect(onOpenChange).not.toHaveBeenCalledWith(false)
  })

  it('closes after a real operational save', async () => {
    const onOpenChange = vi.fn()
    renderDialog({
      canEditProgress: true,
      onOpenChange,
      onSaveOperational: vi.fn(async () => true),
    })

    await userEvent.click(screen.getByRole('button', { name: 'Lưu dòng' }))
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('offers "So sánh" only when both the catalog and the line have images', () => {
    attachments.byEntity = { purchase_request_line_image: [image(21, 'thuc-te.jpg')] }
    renderDialog()
    //  Thiếu ảnh gốc (sản phẩm không có ảnh, cũng không có ảnh đại diện) -> không có gì để so.
    expect(screen.queryByRole('button', { name: 'So sánh' })).toBeNull()
  })

  it('"So sánh" opens a split view: catalog image on one side, line image on the other', async () => {
    attachments.byEntity = {
      product: [image(11, 'goc-1.jpg'), image(12, 'goc-2.jpg')],
      purchase_request_line_image: [image(21, 'thuc-te.jpg')],
    }
    renderDialog()

    await userEvent.click(screen.getByRole('button', { name: 'So sánh' }))

    const original = screen.getByRole('region', { name: 'Ảnh gốc (catalog)' })
    const actual = screen.getByRole('region', { name: 'Ảnh đối chiếu (thực tế)' })
    expect(within(original).getByText('goc-1.jpg — 1/2')).toBeInTheDocument()
    expect(within(actual).getByText('thuc-te.jpg — 1/1')).toBeInTheDocument()
    //  Mỗi bên tự chuyển ảnh; bên chỉ có một ảnh thì không có nút chuyển.
    expect(within(actual).queryByRole('button', { name: /Ảnh sau/ })).toBeNull()

    await userEvent.click(within(original).getByRole('button', { name: /Ảnh sau/ }))
    expect(within(original).getByText('goc-2.jpg — 2/2')).toBeInTheDocument()
    //  Vòng lại khi vượt cuối, như v1.
    await userEvent.click(within(original).getByRole('button', { name: /Ảnh sau/ }))
    expect(within(original).getByText('goc-1.jpg — 1/2')).toBeInTheDocument()
    expect(within(actual).getByText('thuc-te.jpg — 1/1')).toBeInTheDocument()
  })

  it('the catalog thumbnail counts as the original image when the product has no attachment', () => {
    attachments.byEntity = { purchase_request_line_image: [image(21, 'thuc-te.jpg')] }
    renderDialog({ item: { ...ITEM, product_thumbnail_url: '/files/dai-dien.jpg' } })
    expect(screen.getByRole('button', { name: 'So sánh' })).toBeInTheDocument()
  })

  it('deleting a line image asks like v1: "Xác nhận", the file name, Đồng ý / Hủy', async () => {
    attachments.byEntity = { purchase_request_line_image: [image(21, 'thuc-te.jpg')] }
    renderDialog({ canManageAttachments: true })

    await userEvent.click(screen.getByRole('button', { name: 'Xóa ảnh' }))
    const dialog = screen.getByRole('alertdialog')
    expect(within(dialog).getByText('Xác nhận')).toBeInTheDocument()
    expect(within(dialog).getByText('Xóa ảnh "thuc-te.jpg"?')).toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Hủy' })).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Đồng ý' }))

    expect(attachments.remove).toHaveBeenCalledWith(21)
  })
})
