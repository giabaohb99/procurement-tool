import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PurchaseOrderDetail, PurchaseOrderItem } from '../types/purchase-order-detail'
import { createEmptyPurchaseOrder } from '../utils/purchase-order-draft'
import { PurchaseOrderPriceAdjustDialog } from './purchase-order-price-adjust-dialog'

/**
 * bao-CR-794 — hộp Sửa giá sau duyệt của Đơn mua hàng. Chỉ thay tầng gọi API; hook, luật đổi giá
 * và ô số chạy thật để bài kiểm thấy đúng thân lệnh màn hình gửi lên.
 */

const { adjustPrices, toastSuccess } = vi.hoisted(() => ({
  adjustPrices: vi.fn(),
  toastSuccess: vi.fn(),
}))
vi.mock('../api/purchase-order-api', () => ({ purchaseOrderApi: { adjustPrices } }))
vi.mock('sonner', () => ({
  toast: { success: (message: string) => toastSuccess(message), error: vi.fn() },
}))

function line(overrides: Partial<PurchaseOrderItem>): PurchaseOrderItem {
  return {
    product_code: 'VT01',
    product_name: 'Vật tư 01',
    unit: 'Cái',
    qty_request: 10,
    qty_order: 10,
    qty_received: 0,
    price: 4250,
    vat: 8,
    currency: '',
    exchange_rate: 0,
    progress_status: 'ordered',
    deliveries: [],
    ...overrides,
  } as PurchaseOrderItem
}

const ORDER: PurchaseOrderDetail = {
  ...createEmptyPurchaseOrder(),
  id: 77,
  code: 'PO00077',
  status: 'received',
  items: [
    line({ id: 11, product_code: 'VT01', product_name: 'Vật tư 01', price: 4250, qty_received: 4, progress_status: 'received' }),
    line({ id: 12, product_code: 'VT02', product_name: 'Vật tư 02', price: 1350 }),
    line({ id: 13, product_code: 'VT03', product_name: 'Vật tư 03', price: 900, qty_received: 10, progress_status: 'completed' }),
    line({ id: 14, product_code: 'VT04', product_name: 'Vật tư 04', price: 700, progress_status: 'cancelled' }),
    line({ id: 15, product_code: 'VT05', product_name: 'Vật tư 05', price: 2000, qty_received: 2, progress_status: 'paused' }),
  ],
}

function renderDialog(order: PurchaseOrderDetail = ORDER) {
  const onClose = vi.fn()
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  render(
    <QueryClientProvider client={queryClient}>
      <PurchaseOrderPriceAdjustDialog order={order} onClose={onClose} />
    </QueryClientProvider>,
  )
  return { onClose, user: userEvent.setup() }
}

/** Ô Đơn giá mới theo số thứ tự dòng TRÊN ĐƠN. */
function priceInput(lineNumber: number): HTMLInputElement {
  return screen.getByRole('textbox', { name: `Đơn giá mới dòng ${lineNumber}` })
}

function saveButton(): HTMLElement {
  return screen.getByRole('button', { name: 'Lưu giá mới' })
}

function reasonBox(): HTMLElement {
  return screen.getByRole('textbox', { name: /Lý do sửa giá/ })
}

async function typePrice(user: ReturnType<typeof userEvent.setup>, lineNumber: number, text: string) {
  const input = priceInput(lineNumber)
  await user.clear(input)
  if (text) await user.type(input, text)
}

beforeEach(() => {
  adjustPrices.mockReset()
  toastSuccess.mockReset()
})

describe('PurchaseOrderPriceAdjustDialog', () => {
  it('lists only the lines that are neither completed nor cancelled, keeping their order line numbers', () => {
    renderDialog()
    const table = screen.getByRole('table')
    //  Một hàng tiêu đề + ba dòng còn sửa giá được (dòng 1, 2 và dòng Tạm ngưng số 5).
    expect(within(table).getAllByRole('row')).toHaveLength(4)
    expect(within(table).getByText('VT01')).toBeInTheDocument()
    expect(within(table).getByText('VT02')).toBeInTheDocument()
    expect(within(table).getByText('VT05')).toBeInTheDocument()
    expect(within(table).queryByText('VT03')).toBeNull()
    expect(within(table).queryByText('VT04')).toBeNull()
    expect(screen.queryByRole('textbox', { name: 'Đơn giá mới dòng 3' })).toBeNull()
    expect(screen.queryByRole('textbox', { name: 'Đơn giá mới dòng 4' })).toBeNull()
    //  Ô giá mới điền sẵn giá hiện tại.
    expect(priceInput(1).value).toBe('4.250')
    expect(priceInput(2).value).toBe('1.350')
    expect(priceInput(5).value).toBe('2.000')
  })

  it('says so instead of drawing an empty table when every line is already closed', () => {
    renderDialog({
      ...ORDER,
      items: ORDER.items.filter((item) => ['completed', 'cancelled'].includes(item.progress_status ?? '')),
    })
    expect(screen.queryByRole('table')).toBeNull()
    expect(screen.getByText(/Đơn không còn dòng nào sửa giá được/)).toBeInTheDocument()
    expect(saveButton()).toBeDisabled()
  })

  it('keeps the save button locked until a price changed AND a reason is typed', async () => {
    const { user } = renderDialog()
    expect(saveButton()).toBeDisabled()

    //  Có lý do mà chưa đổi giá dòng nào.
    await user.type(reasonBox(), 'NCC báo lại giá')
    expect(saveButton()).toBeDisabled()

    //  Đổi giá mà xóa lý do (chỉ còn khoảng trắng).
    await typePrice(user, 1, '5000')
    expect(saveButton()).toBeEnabled()
    await user.clear(reasonBox())
    await user.type(reasonBox(), '   ')
    expect(saveButton()).toBeDisabled()

    //  Gõ lại đúng giá cũ thì coi như chưa đổi.
    await user.type(reasonBox(), 'NCC báo lại giá')
    await typePrice(user, 1, '4250')
    expect(saveButton()).toBeDisabled()
    expect(adjustPrices).not.toHaveBeenCalled()
  })

  it('sends the reason and ONLY the changed lines, shows the server message and closes', async () => {
    const serverMessage =
      'Đã sửa giá 1 dòng. Kiểm lại số tiền trên yêu cầu thanh toán đang Nháp: YCTT00126'
    adjustPrices.mockResolvedValue({ order: ORDER, message: serverMessage })
    const { user, onClose } = renderDialog()

    await typePrice(user, 1, '5000')
    await user.type(reasonBox(), '  NCC báo lại giá sau khi hàng về ')
    await user.click(saveButton())

    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1))
    expect(adjustPrices).toHaveBeenCalledTimes(1)
    expect(adjustPrices).toHaveBeenCalledWith(77, {
      reason: 'NCC báo lại giá sau khi hàng về',
      items: [{ id: 11, price: 5000 }],
    })
    //  Câu báo là NGUYÊN câu của máy chủ — phần nhắc YCTT Nháp nằm trong đó.
    expect(toastSuccess).toHaveBeenCalledWith(serverMessage)
  })

  it('sends several changed lines in one request and keeps decimal prices', async () => {
    adjustPrices.mockResolvedValue({ order: ORDER, message: 'Đã sửa giá 2 dòng' })
    const { user, onClose } = renderDialog()

    await typePrice(user, 2, '1.668,1825')
    await typePrice(user, 5, '1900')
    await user.type(reasonBox(), 'Giá quyết toán')
    await user.click(saveButton())

    await waitFor(() => expect(onClose).toHaveBeenCalled())
    expect(adjustPrices).toHaveBeenCalledWith(77, {
      reason: 'Giá quyết toán',
      items: [
        { id: 12, price: 1668.1825 },
        { id: 15, price: 1900 },
      ],
    })
  })

  it('refuses to send while any line has a price of zero, even if another line is valid', async () => {
    const { user } = renderDialog()
    await typePrice(user, 1, '5000')
    await user.type(reasonBox(), 'NCC báo lại giá')
    expect(saveButton()).toBeEnabled()

    //  Xóa trắng ô giá của dòng 2 -> giá 0.
    await typePrice(user, 2, '')
    expect(screen.getByText('Đơn giá mới phải lớn hơn 0.')).toBeInTheDocument()
    expect(saveButton()).toBeDisabled()
    await user.click(saveButton())
    expect(adjustPrices).not.toHaveBeenCalled()

    //  Ô số chặn dấu trừ: gõ "-5" thành 5, không thể lọt giá âm lên máy chủ.
    await typePrice(user, 2, '-5')
    expect(priceInput(2).value).toBe('5')
    await typePrice(user, 2, '0')
    expect(saveButton()).toBeDisabled()
  })

  it('stays open when the server refuses, so the user can fix and retry', async () => {
    adjustPrices.mockRejectedValue(new Error('Công nợ hàng của đơn đã trả tiền — không sửa giá được.'))
    const { user, onClose } = renderDialog()

    await typePrice(user, 1, '5000')
    await user.type(reasonBox(), 'NCC báo lại giá')
    await user.click(saveButton())

    await waitFor(() => expect(adjustPrices).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(saveButton()).toBeEnabled())
    expect(onClose).not.toHaveBeenCalled()
    expect(toastSuccess).not.toHaveBeenCalled()
    //  Giá và lý do vừa gõ còn nguyên.
    expect(priceInput(1).value).toBe('5.000')
    expect(reasonBox()).toHaveValue('NCC báo lại giá')
  })

  it('shows the amount difference by RECEIVED quantity and a dash for lines not received yet', async () => {
    const { user } = renderDialog()
    await typePrice(user, 1, '5000')
    await typePrice(user, 2, '2000')
    //  Rời ô để ô số hiện lại bản đã định dạng.
    await user.click(reasonBox())

    const rows = within(screen.getByRole('table')).getAllByRole('row')
    //  Dòng 1: đã nhận 4 × (5.000 − 4.250) = +3.000 đ.
    expect(within(rows[1]).getByText('+3.000 đ')).toBeInTheDocument()
    //  Dòng 2: chưa nhận hàng -> gạch, dù đã đổi giá.
    expect(within(rows[2]).getByText('—')).toBeInTheDocument()
    //  Dòng 5 không đổi giá -> 0 đ.
    expect(within(rows[3]).getByText('0 đ')).toBeInTheDocument()
    expect(screen.getByText(/Đang đổi giá/)).toHaveTextContent(
      'Đang đổi giá 2 dòng. Tiền hàng đã nhận (chưa VAT) thay đổi +3.000 đ.',
    )
  })

  it('closes on Hủy without calling the server', async () => {
    const { user, onClose } = renderDialog()
    await typePrice(user, 1, '5000')
    await user.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(onClose).toHaveBeenCalledTimes(1)
    expect(adjustPrices).not.toHaveBeenCalled()
  })
})
