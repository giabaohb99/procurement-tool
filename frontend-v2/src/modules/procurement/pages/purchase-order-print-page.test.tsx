import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type * as ReactRouterModule from 'react-router-dom'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

type ReactRouter = typeof ReactRouterModule

import type { PurchaseOrderPrintData } from '../api/purchase-order-api'
import { PurchaseOrderPrintPage } from './purchase-order-print-page'

const printData = vi.hoisted(() => ({ current: null as unknown }))

vi.mock('../hooks/use-purchase-order', () => ({
  usePurchaseOrderPrintData: () => ({
    data: printData.current,
    isLoading: false,
    isError: printData.current === null,
  }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<ReactRouter>('react-router-dom')
  return { ...actual, useParams: () => ({ id: '7' }) }
})

function makeData(overrides: Partial<PurchaseOrderPrintData> = {}): PurchaseOrderPrintData {
  return {
    id: 7,
    code: 'PO-2026-0007',
    order_date: '2026-08-31',
    supplier_name: 'NCC Một',
    items: [],
    company: {},
    supplier: {},
    warehouse: {},
    wh_names: {},
    signers: {
      creator_name: 'Nguyen Van Lap',
      creator_signature: 'https://cdn/ky-lap.png',
      approver_name: 'Tran Thi Duyet',
      approver_signature: 'https://cdn/ky-duyet.png',
    },
    ...overrides,
  } as PurchaseOrderPrintData
}

function renderPage(data: PurchaseOrderPrintData | null) {
  printData.current = data
  return render(
    <MemoryRouter>
      <PurchaseOrderPrintPage />
    </MemoryRouter>,
  )
}

describe('PurchaseOrderPrintPage — công tắc chữ ký', () => {
  it('shows both signature images by default', () => {
    renderPage(makeData())

    expect(screen.getByAltText('Chữ ký Người lập')).toHaveAttribute('src', 'https://cdn/ky-lap.png')
    expect(screen.getByAltText('Chữ ký Trưởng bộ phận')).toHaveAttribute(
      'src',
      'https://cdn/ky-duyet.png',
    )
  })

  it('drops the images but keeps the names when switching to "Không chữ ký"', async () => {
    const user = userEvent.setup()
    renderPage(makeData())

    await user.click(screen.getByRole('button', { name: 'Không chữ ký' }))

    expect(screen.queryByAltText('Chữ ký Người lập')).not.toBeInTheDocument()
    expect(screen.queryByAltText('Chữ ký Trưởng bộ phận')).not.toBeInTheDocument()
    // Họ tên vẫn phải in: ô ghi "(Ký, ghi rõ họ tên)", bỏ tên đi thì người ký tay
    // không biết ô đó là của ai.
    expect(screen.getByText('Nguyen Van Lap')).toBeInTheDocument()
    expect(screen.getByText('Tran Thi Duyet')).toBeInTheDocument()
  })

  it('keeps the signature choice when switching between the two forms', async () => {
    const user = userEvent.setup()
    renderPage(makeData())

    await user.click(screen.getByRole('button', { name: 'Không chữ ký' }))
    await user.click(screen.getByRole('button', { name: 'Đơn mua hàng (nội bộ)' }))

    expect(screen.queryByAltText('Chữ ký Người lập')).not.toBeInTheDocument()
    expect(screen.getByText('Trưởng phòng / Trưởng BP')).toBeInTheDocument()
  })

  it('leaves the "Người nhận" box empty on the internal form — nobody signs it in the system', async () => {
    const user = userEvent.setup()
    renderPage(makeData())

    await user.click(screen.getByRole('button', { name: 'Đơn mua hàng (nội bộ)' }))

    expect(screen.getByText('Người nhận')).toBeInTheDocument()
    expect(screen.queryByAltText('Chữ ký Người nhận')).not.toBeInTheDocument()
  })

  it('renders an unapproved order without an approver signature or name', () => {
    renderPage(
      makeData({
        signers: {
          creator_name: 'Nguyen Van Lap',
          creator_signature: 'https://cdn/ky-lap.png',
          approver_name: '',
          approver_signature: '',
        },
      }),
    )

    expect(screen.getByAltText('Chữ ký Người lập')).toBeInTheDocument()
    expect(screen.queryByAltText('Chữ ký Trưởng bộ phận')).not.toBeInTheDocument()
    // Ô ký vẫn còn để ký tay, chỉ trống ruột.
    expect(screen.getByText('Trưởng bộ phận')).toBeInTheDocument()
  })

  it('renders an old order whose payload carries no signers block at all', () => {
    renderPage(makeData({ signers: undefined }))

    expect(screen.queryByAltText('Chữ ký Người lập')).not.toBeInTheDocument()
    expect(screen.getByText('Người lập')).toBeInTheDocument()
  })
})

// bao-CR-410 (ticket prod 52) — phiếu ĐƠN ĐẶT HÀNG phải bày phân loại hàng hóa.
describe('PurchaseOrderPrintPage — cột Phân loại của phiếu Đơn đặt hàng', () => {
  function makeLine(item_group: string) {
    return makeData({
      items: [
        {
          id: 1,
          product_code: 'NHG5218',
          product_name: 'Nhãn giấy',
          item_group,
          spec: '',
          unit: 'Cái',
          qty_order: 100,
          price: 1000,
          vat: 8,
          warehouse_code: 'KHO01',
          invoice_name: '',
          note: '',
        },
      ],
    } as Partial<PurchaseOrderPrintData>)
  }

  it('prints the item group between the code and the product name', () => {
    renderPage(makeLine('Bao bì'))

    const headers = screen.getAllByRole('columnheader').map((th) => th.textContent)
    expect(headers.slice(0, 4)).toEqual(['STT', 'Mã', 'Phân loại', 'Tên hàng hóa'])
    expect(screen.getByRole('cell', { name: 'Bao bì' })).toBeInTheDocument()
  })

  it('keeps the TỔNG CỘNG row aligned with the header after the new column', () => {
    // Thêm cột mà quên sửa `colSpan` thì số tổng tụt sang ô khác — bảng vẫn dựng được,
    // không lỗi nào đỏ lên, chỉ có con số nằm dưới sai tiêu đề trên bản in đưa cho NCC.
    renderPage(makeLine('Bao bì'))

    const headerCount = screen.getAllByRole('columnheader').length
    const totalCell = screen.getByRole('cell', { name: 'TỔNG CỘNG' })
    const totalRow = totalCell.closest('tr')
    const span = (cell: Element) => Number(cell.getAttribute('colspan') ?? 1)
    const spanned = Array.from(totalRow?.children ?? []).reduce((sum, c) => sum + span(c), 0)

    expect(spanned).toBe(headerCount)
    // Ô tiền đứng ngay sau khối gộp, tức đúng cột "Thành tiền" (cột thứ 11).
    expect(span(totalCell)).toBe(headerCount - 4)
  })

  it('leaves the cell blank for a line with no item group instead of printing undefined', () => {
    renderPage(makeLine(''))

    const headers = screen.getAllByRole('columnheader').map((th) => th.textContent)
    expect(headers).toContain('Phân loại')
    expect(screen.queryByText('undefined')).not.toBeInTheDocument()
  })
})
