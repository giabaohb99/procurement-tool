import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type {
  PrintSignatureCell,
  PurchaseRequestDetail,
  PurchaseRequestItem,
} from '../types/purchase-request-detail'
import type { PrintSignatureSource } from '../utils/purchase-request-signature-cells'
import {
  PurchaseRequestPrintOptions,
  PurchaseRequestPrintSheet,
  SignatureSection,
} from './purchase-request-print-page'

// bao-CR-531: cụm «XÉT DUYỆT» vẽ 2, 3 hoặc 4 ô theo backend; «Không chữ ký» bỏ cả tên lẫn ảnh.

function makeSource(cells?: PrintSignatureCell[]): PrintSignatureSource {
  return {
    requester: 'Nguoi Lap',
    requester_signature: 'https://cdn/ky-lap.png',
    approver_name: 'Le Phuoc Huu',
    approver_signature: 'https://cdn/ky-huu.png',
    purchasing_head_name: 'Pham Khanh Ngan',
    purchasing_head_signature: '',
    print_signature_cells: cells,
  }
}

const fourCells: PrintSignatureCell[] = [
  { key: 'director', role: 'Giám đốc', name: '', signature: '' },
  { key: 'purchasing_head', role: 'TP/BP mua hàng', name: 'Pham Khanh Ngan', signature: '' },
  { key: 'proposer', role: 'TP/BP đề xuất', name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' },
  { key: 'preparer', role: 'Người lập', name: 'Nguoi Lap', signature: 'https://cdn/ky-lap.png' },
]

//  bao-CR-536 — ca ICARE: đại diện = TP/BP đề xuất → tên lên «Giám đốc», ô đề xuất GIỮ nhưng trống.
const icareCells: PrintSignatureCell[] = [
  { key: 'director', role: 'Giám đốc', name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' },
  { key: 'purchasing_head', role: 'TP/BP mua hàng', name: 'Pham Khanh Ngan', signature: '' },
  { key: 'proposer', role: 'TP/BP đề xuất', name: '', signature: '' },
  { key: 'preparer', role: 'Người lập', name: 'Nguoi Lap', signature: 'https://cdn/ky-lap.png' },
]

//  bao-CR-539 — hộ kinh doanh 4 ô như công ty, chỉ đổi nhãn ô đầu thành «Chủ hộ»; có tên.
const householdCells: PrintSignatureCell[] = [
  { key: 'household_owner', role: 'Chủ hộ', name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' },
  { key: 'purchasing_head', role: 'TP/BP mua hàng', name: 'Pham Khanh Ngan', signature: '' },
  { key: 'proposer', role: 'TP/BP đề xuất', name: '', signature: '' },
  { key: 'preparer', role: 'Người lập', name: 'Nguoi Lap', signature: 'https://cdn/ky-lap.png' },
]

function renderSection(cells: PrintSignatureCell[] | undefined, showSignature = true, taxMode = false) {
  const view = render(
    <SignatureSection purchaseRequest={makeSource(cells)} taxMode={taxMode} showSignature={showSignature} />,
  )
  const grid = view.container.querySelector('.pr-print-signature-grid') as HTMLElement
  return { ...view, grid }
}

describe('SignatureSection', () => {
  it('draws four cells with a blank director when nobody merges', () => {
    const { grid } = renderSection(fourCells)
    expect(within(grid).getAllByText('(Ký, ghi rõ họ tên)')).toHaveLength(4)
    expect(grid.style.getPropertyValue('--pr-signature-columns')).toBe('4')
    expect(screen.getAllByRole('img')).toHaveLength(2)
  })

  it('keeps all four cells and puts the legal representative into «Giám đốc» (ICARE case)', () => {
    //  bao-CR-531 bỏ hẳn ô «TP/BP đề xuất» — đại ca báo thiếu ô (PYC29092603). Nay ô vẫn có, chỉ trống.
    const { grid } = renderSection(icareCells)
    expect(screen.getByText('TP/BP đề xuất')).toBeInTheDocument()
    expect(within(grid).getAllByText('(Ký, ghi rõ họ tên)')).toHaveLength(4)
    expect(grid.style.getPropertyValue('--pr-signature-columns')).toBe('4')
    expect(screen.getByAltText('Chữ ký Giám đốc')).toHaveAttribute('src', 'https://cdn/ky-huu.png')
    expect(screen.getAllByText('Le Phuoc Huu')).toHaveLength(1)
  })

  it('draws four cells for a household business, first one labelled «Chủ hộ», with names', () => {
    //  PYC29092604 (DR.XANH): bản 536 ra 3 ô, đại ca báo «còn thiếu phần TP bên thu mua».
    const { grid } = renderSection(householdCells)
    expect(screen.getByText('Chủ hộ')).toBeInTheDocument()
    expect(screen.getByText('TP/BP mua hàng')).toBeInTheDocument()
    expect(screen.getByText('TP/BP đề xuất')).toBeInTheDocument()
    expect(screen.queryByText('Giám đốc')).toBeNull()
    expect(screen.getByText('Le Phuoc Huu')).toBeInTheDocument()
    expect(screen.getByText('Pham Khanh Ngan')).toBeInTheDocument()
    expect(screen.getByText('Nguoi Lap')).toBeInTheDocument()
    expect(grid.style.getPropertyValue('--pr-signature-columns')).toBe('4')
  })

  it('"Không chữ ký" removes names as well as images', () => {
    renderSection(icareCells, false)
    expect(screen.queryByRole('img')).toBeNull()
    expect(screen.queryByText('Le Phuoc Huu')).toBeNull()
    expect(screen.queryByText('Nguoi Lap')).toBeNull()
    expect(screen.getByText('Giám đốc')).toBeInTheDocument()
  })

  it('tax template keeps the backend cell set but blanks everything', () => {
    renderSection(householdCells, true, true)
    expect(screen.queryByRole('img')).toBeNull()
    expect(screen.queryByText('Le Phuoc Huu')).toBeNull()
    expect(screen.queryByText('Nguoi Lap')).toBeNull()
    expect(screen.getByText('Chủ hộ')).toBeInTheDocument()
    expect(screen.getByText('TP/BP mua hàng')).toBeInTheDocument()
    expect(screen.queryByText('Pham Khanh Ngan')).toBeNull()
  })

  it('falls back to the legacy four cells when the backend has no cell list', () => {
    renderSection(undefined)
    for (const role of ['Giám đốc', 'TP/BP mua hàng', 'TP/BP đề xuất', 'Người lập']) {
      expect(screen.getByText(role)).toBeInTheDocument()
    }
    expect(screen.getByText('Le Phuoc Huu')).toBeInTheDocument()
  })
})

// bao-CR-544 → bao-CR-546 — ô tick «Ẩn nơi giao»: GIỮ cột «Nơi giao» (khuôn mẫu không đổi), chỉ để
// trống chữ. Bản CR-544 xóa hẳn cột, đại ca chê lệch khuôn (ảnh PYC29092603).
function makeItem(id: number, warehouse: string): PurchaseRequestItem {
  //  why: tờ phiếu chỉ đọc vài trường của dòng — dựng đủ kiểu dòng YCMH ở đây là nhiễu.
  return {
    id,
    product_name: `Hàng ${id}`,
    product_code: `MH${id}`,
    unit: 'Cái',
    qty: 2,
    price: 1000,
    vat_pct: 8,
    warehouse,
    note: '',
    need_date: '',
    chosen_option: null,
  } as unknown as PurchaseRequestItem
}

function renderSheet(hideDeliveryPlace?: boolean) {
  const items = [makeItem(1, 'Kho Bình Dương'), makeItem(2, 'Kho Long An')]
  //  why: như trên — tờ phiếu chỉ cần phần đầu phiếu + nguồn chữ ký.
  const purchaseRequest = {
    ...makeSource(fourCells),
    code: 'PYC01',
    company_name: 'DEGO',
    request_date: '2026-10-01',
    items,
  } as unknown as PurchaseRequestDetail
  const view = render(
    <PurchaseRequestPrintSheet
      purchaseRequest={purchaseRequest}
      items={items}
      supplier={{ name: '', tax_code: '', contact: '' }}
      warehouseCode={(name) => (name === 'Kho Bình Dương' ? 'KBD' : 'KLA')}
      taxMode={false}
      showSignature
      hideDeliveryPlace={hideDeliveryPlace}
    />,
  )
  const table = view.container.querySelector('.pr-print-items') as HTMLTableElement
  return { ...view, table }
}

function rowWidths(table: HTMLTableElement): number[] {
  return Array.from(table.rows).map((row) =>
    Array.from(row.cells).reduce((sum, cell) => sum + (cell.colSpan || 1), 0),
  )
}

describe('PurchaseRequestPrintSheet — hide delivery place (bao-CR-546)', () => {
  it('prints the delivery place by default, as before', () => {
    const { table } = renderSheet()
    expect(within(table).getByRole('columnheader', { name: 'Nơi giao' })).toBeInTheDocument()
    expect(within(table).getByText('KBD')).toBeInTheDocument()
    expect(within(table).getByText('KLA')).toBeInTheDocument()
  })

  it('hiding keeps the column, its header and width, and only blanks the cells', () => {
    const { table } = renderSheet(true)
    expect(within(table).getByRole('columnheader', { name: 'Nơi giao' })).toBeInTheDocument()
    expect(table.querySelector('col.pr-print-col-place')).not.toBeNull()
    expect(within(table).queryByText('KBD')).toBeNull()
    expect(within(table).queryByText('KLA')).toBeNull()
    //  Khuôn giữ nguyên 9 cột ở MỌI hàng, kể cả ba dòng tổng (bản CR-544 rút còn 8 — sai ý đại ca).
    expect(table.querySelectorAll('col')).toHaveLength(9)
    expect(new Set(rowWidths(table))).toEqual(new Set([9]))
  })

  it('the place cell of each line is empty, not removed', () => {
    const { table } = renderSheet(true)
    const headerCells = Array.from(table.tHead?.rows[0].cells ?? [])
    const placeIndex = headerCells.findIndex((cell) => cell.textContent === 'Nơi giao')
    const firstLine = table.tBodies[0].rows[0]
    expect(placeIndex).toBe(7)
    expect(firstLine.cells[placeIndex].textContent).toBe('')
    expect(firstLine.cells).toHaveLength(9)
  })
})

describe('PurchaseRequestPrintOptions (bao-CR-546)', () => {
  it('shows one template picker with the default template and an unticked hide-place box', () => {
    render(
      <PurchaseRequestPrintOptions
        template="normal-signed"
        onTemplateChange={vi.fn()}
        hideDeliveryPlace={false}
        onHideDeliveryPlaceChange={vi.fn()}
      />,
    )
    expect(screen.getByRole('combobox', { name: 'Mẫu in' })).toHaveTextContent('Mẫu thường – có chữ ký')
    expect(screen.getByRole('checkbox', { name: 'Ẩn nơi giao' })).not.toBeChecked()
    //  Hai nhóm nút cũ đã bỏ hẳn — còn sót là thanh nút lại nhảy khi đổi mẫu.
    expect(screen.queryByRole('button', { name: 'Không chữ ký' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Mẫu thuế' })).toBeNull()
  })

  it('the tax template keeps the same controls in place', () => {
    render(
      <PurchaseRequestPrintOptions
        template="tax"
        onTemplateChange={vi.fn()}
        hideDeliveryPlace
        onHideDeliveryPlaceChange={vi.fn()}
      />,
    )
    expect(screen.getByRole('combobox', { name: 'Mẫu in' })).toHaveTextContent('Mẫu thuế')
    expect(screen.getByRole('checkbox', { name: 'Ẩn nơi giao' })).toBeChecked()
  })

  it('ticking the box reports true, unticking reports false', async () => {
    const onChange = vi.fn()
    const { rerender } = render(
      <PurchaseRequestPrintOptions
        template="normal-signed"
        onTemplateChange={vi.fn()}
        hideDeliveryPlace={false}
        onHideDeliveryPlaceChange={onChange}
      />,
    )
    await userEvent.click(screen.getByRole('checkbox', { name: 'Ẩn nơi giao' }))
    expect(onChange).toHaveBeenLastCalledWith(true)
    rerender(
      <PurchaseRequestPrintOptions
        template="normal-signed"
        onTemplateChange={vi.fn()}
        hideDeliveryPlace
        onHideDeliveryPlaceChange={onChange}
      />,
    )
    await userEvent.click(screen.getByRole('checkbox', { name: 'Ẩn nơi giao' }))
    expect(onChange).toHaveBeenLastCalledWith(false)
  })
})
