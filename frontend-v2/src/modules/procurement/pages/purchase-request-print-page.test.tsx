import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type {
  PrintSignatureCell,
  PurchaseRequestDetail,
  PurchaseRequestItem,
} from '../types/purchase-request-detail'
import type { PurchasingPrintData } from '../types/purchasing-print'
import { listPrintTemplates } from '../utils/purchase-request-print-template'
import type { PrintSignatureSource } from '../utils/purchase-request-signature-cells'
import {
  PurchaseRequestPrintOptions,
  PurchaseRequestPrintSheet,
  SignatureSection,
} from './purchase-request-print-page'

// bao-CR-531: cụm "XÉT DUYỆT" vẽ 2, 3 hoặc 4 ô theo backend; "Không chữ ký" bỏ cả tên lẫn ảnh.

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

//  bao-CR-536 — ca ICARE: đại diện = TP/BP đề xuất → tên lên "Giám đốc", ô đề xuất GIỮ nhưng trống.
const icareCells: PrintSignatureCell[] = [
  { key: 'director', role: 'Giám đốc', name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' },
  { key: 'purchasing_head', role: 'TP/BP mua hàng', name: 'Pham Khanh Ngan', signature: '' },
  { key: 'proposer', role: 'TP/BP đề xuất', name: '', signature: '' },
  { key: 'preparer', role: 'Người lập', name: 'Nguoi Lap', signature: 'https://cdn/ky-lap.png' },
]

//  bao-CR-539 — hộ kinh doanh 4 ô như công ty, chỉ đổi nhãn ô đầu thành "Chủ hộ"; có tên.
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

  it('keeps all four cells and puts the legal representative into "Giám đốc" (ICARE case)', () => {
    //  bao-CR-531 bỏ hẳn ô "TP/BP đề xuất" — đại ca báo thiếu ô (PYC29092603). Nay ô vẫn có, chỉ trống.
    const { grid } = renderSection(icareCells)
    expect(screen.getByText('TP/BP đề xuất')).toBeInTheDocument()
    expect(within(grid).getAllByText('(Ký, ghi rõ họ tên)')).toHaveLength(4)
    expect(grid.style.getPropertyValue('--pr-signature-columns')).toBe('4')
    expect(screen.getByAltText('Chữ ký Giám đốc')).toHaveAttribute('src', 'https://cdn/ky-huu.png')
    expect(screen.getAllByText('Le Phuoc Huu')).toHaveLength(1)
  })

  it('draws four cells for a household business, first one labelled "Chủ hộ", with names', () => {
    //  PYC29092604 (DR.XANH): bản 536 ra 3 ô, đại ca báo "còn thiếu phần TP bên thu mua".
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

// bao-CR-544 → bao-CR-546 — ô tick "Ẩn nơi giao": GIỮ cột "Nơi giao" (khuôn mẫu không đổi), chỉ để
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

function renderSheet(
  hideDeliveryPlace?: boolean,
  extra: { purchasing?: PurchasingPrintData; showSignature?: boolean } = {},
) {
  const items = [makeItem(1, 'Kho Bình Dương'), makeItem(2, 'Kho Long An')]
  //  why: như trên — tờ phiếu chỉ cần phần đầu phiếu + nguồn chữ ký.
  const purchaseRequest = {
    ...makeSource(fourCells),
    code: 'PYC01',
    company_name: 'DEGO',
    request_date: '2026-10-01',
    requester: 'Nguoi Lap',
    requester_position: 'Nhân viên',
    department: 'Phòng Kỹ thuật',
    head_of_dept: 'Truong Phong YCMH',
    items,
  } as unknown as PurchaseRequestDetail
  const view = render(
    <PurchaseRequestPrintSheet
      purchaseRequest={purchaseRequest}
      items={items}
      supplier={{ name: '', tax_code: '', contact: '' }}
      warehouseCode={(name) => (name === 'Kho Bình Dương' ? 'KBD' : 'KLA')}
      taxMode={false}
      showSignature={extra.showSignature ?? true}
      hideDeliveryPlace={hideDeliveryPlace}
      purchasing={extra.purchasing}
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

// duoc-CR-777 — mẫu thu mua: người đang in + quản lý trực tiếp, bảng hàng + tổng theo ĐƠN.
const purchasingData: PurchasingPrintData = {
  po_id: 9,
  po_code: 'DMH01',
  order_date: '2026-11-17',
  currency: 'VND',
  proposer: {
    employee_id: 7,
    name: 'Nguyen Thu Mua',
    position: 'Nhân viên thu mua',
    department: 'Phòng Thu mua',
    signature: 'https://cdn/ky-thu-mua.png',
  },
  manager: { employee_id: 8, name: 'Tran Quan Ly', position: 'Trưởng phòng', signature: 'https://cdn/ky-quan-ly.png' },
  supplier: { code: 'S1', name: 'NCC Don' },
  supplier_hidden: false,
  items: [
    {
      line_id: 31,
      product_code: 'MH2',
      product_name: 'Hàng trên đơn',
      invoice_name: '',
      spec: '',
      item_group: '',
      unit: 'Thùng',
      qty: 5,
      price: 30000,
      vat: 10,
      amount: 165000,
    },
  ],
  subtotal: 150000,
  vat: 15000,
  total: 165000,
}

describe('PurchaseRequestPrintSheet — purchasing template (duoc-CR-777)', () => {
  it('general info shows the person printing and their direct manager', () => {
    const { container } = renderSheet(false, { purchasing: purchasingData })
    const text = container.textContent ?? ''
    expect(text).toContain('Người đề xuất: Nguyen Thu Mua')
    expect(text).toContain('Chức vụ: Nhân viên thu mua')
    expect(text).toContain('Hiện công tác tại bộ phận: Phòng Thu mua')
    expect(text).toContain('Trưởng phòng ban/bộ phận: Tran Quan Ly')
    expect(text).not.toContain('Truong Phong YCMH')
  })

  it('the items table is the order lines with pre-VAT amounts and the server totals', () => {
    const { table } = renderSheet(false, { purchasing: purchasingData })
    const body = table.tBodies[0]
    //  Một dòng hàng + ba dòng tổng; dòng YCMH (Hàng 1, Hàng 2) không còn.
    expect(body.rows).toHaveLength(4)
    expect(within(table).queryByText('Hàng 1')).toBeNull()
    const cells = Array.from(body.rows[0].cells).map((cell) => cell.textContent)
    expect(cells.slice(0, 7)).toEqual(['1', 'Hàng trên đơn', 'MH2', 'Thùng', '5', '30.000', '150.000'])
    //  Nơi giao mượn của dòng YCMH cùng mã MH2 (Kho Long An -> KLA).
    expect(cells[7]).toBe('KLA')
    expect(body.rows[1].textContent).toContain('150.000')
    expect(body.rows[2].textContent).toContain('15.000')
    expect(body.rows[3].textContent).toContain('165.000')
  })

  it('signed: "Người lập" and "TP/BP đề xuất" carry the new people with their signatures', () => {
    renderSheet(false, { purchasing: purchasingData })
    expect(screen.getByAltText('Chữ ký Người lập')).toHaveAttribute('src', 'https://cdn/ky-thu-mua.png')
    expect(screen.getByAltText('Chữ ký TP/BP đề xuất')).toHaveAttribute('src', 'https://cdn/ky-quan-ly.png')
    expect(screen.queryByText('Le Phuoc Huu')).toBeNull()
    //  Ô "TP/BP mua hàng" giữ như mẫu thường.
    expect(screen.getByText('Pham Khanh Ngan')).toBeInTheDocument()
  })

  it('unsigned: no signature image and no name in any cell', () => {
    const { container } = renderSheet(false, { purchasing: purchasingData, showSignature: false })
    expect(screen.queryByRole('img')).toBeNull()
    const grid = container.querySelector('.pr-print-signature-grid') as HTMLElement
    expect(within(grid).queryByText('Nguyen Thu Mua')).toBeNull()
    expect(within(grid).queryByText('Tran Quan Ly')).toBeNull()
  })

  it('without purchasing data the sheet stays on the request data', () => {
    const { container, table } = renderSheet()
    expect(container.textContent).toContain('Trưởng phòng ban/bộ phận: Truong Phong YCMH')
    expect(within(table).getByText('Hàng 1')).toBeInTheDocument()
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

// bao-CR-574 (đại ca chốt 03/10/2026): nút "In phiếu" luôn mở phiếu chung; người có quyền xem
// nhà cung cấp chọn bản tách ngay trong ô "Mẫu in". Hai nút lẻ cũ đã bỏ.
describe('PurchaseRequestPrintOptions — supplier layout group (bao-CR-574)', () => {
  function renderOptions(props: Partial<Parameters<typeof PurchaseRequestPrintOptions>[0]> = {}) {
    const onTemplateChange = vi.fn()
    const onLayoutChange = vi.fn()
    render(
      <PurchaseRequestPrintOptions
        template="normal-signed"
        onTemplateChange={onTemplateChange}
        onLayoutChange={onLayoutChange}
        hideDeliveryPlace={false}
        onHideDeliveryPlaceChange={vi.fn()}
        {...props}
      />,
    )
    return { onTemplateChange, onLayoutChange }
  }

  it('without supplier permission shows only the three common templates', async () => {
    renderOptions()
    await userEvent.click(screen.getByRole('combobox', { name: 'Mẫu in' }))
    expect(screen.getAllByRole('option')).toHaveLength(3)
    expect(screen.queryByText('Tách theo nhà cung cấp')).toBeNull()
    expect(screen.queryByRole('option', { name: /Theo NCC/ })).toBeNull()
  })

  //  duoc-CR-777: bản in mở từ đơn truyền thêm hai mẫu thu mua — năm lựa chọn, hai mẫu thu mua đứng đầu.
  it('from a purchase order with purchasing data shows five templates', async () => {
    const { onTemplateChange } = renderOptions({ templates: listPrintTemplates(true) })
    await userEvent.click(screen.getByRole('combobox', { name: 'Mẫu in' }))
    expect(screen.getAllByRole('option').map((option) => option.textContent)).toEqual([
      'Mẫu thu mua – có chữ ký',
      'Mẫu thu mua – không chữ ký',
      'Mẫu thường – có chữ ký',
      'Mẫu thường – không chữ ký',
      'Mẫu thuế',
    ])
    await userEvent.click(screen.getByRole('option', { name: 'Mẫu thu mua – không chữ ký' }))
    expect(onTemplateChange).toHaveBeenCalledWith('purchasing-unsigned')
  })

  it('the supplier group never offers purchasing templates', async () => {
    renderOptions({ supplierLayout: { enabled: true }, templates: listPrintTemplates(true) })
    await userEvent.click(screen.getByRole('combobox', { name: 'Mẫu in' }))
    expect(screen.getAllByRole('option')).toHaveLength(6)
    expect(screen.queryByRole('option', { name: /thu mua/ })).toBeNull()
  })

  it('with permission shows both groups, three templates each', async () => {
    renderOptions({ supplierLayout: { enabled: true } })
    await userEvent.click(screen.getByRole('combobox', { name: 'Mẫu in' }))
    expect(screen.getAllByRole('option')).toHaveLength(6)
    expect(screen.getByText('Phiếu chung')).toBeInTheDocument()
    expect(screen.getByText('Tách theo nhà cung cấp')).toBeInTheDocument()
  })

  it('picking a supplier template switches layout and keeps the template', async () => {
    const { onTemplateChange, onLayoutChange } = renderOptions({ supplierLayout: { enabled: true } })
    await userEvent.click(screen.getByRole('combobox', { name: 'Mẫu in' }))
    await userEvent.click(screen.getByRole('option', { name: 'Theo NCC · Mẫu thuế' }))
    expect(onLayoutChange).toHaveBeenCalledWith('supplier', 'tax')
    expect(onTemplateChange).not.toHaveBeenCalled()
  })

  it('picking another template in the same group stays on the page', async () => {
    const { onTemplateChange, onLayoutChange } = renderOptions({ supplierLayout: { enabled: true } })
    await userEvent.click(screen.getByRole('combobox', { name: 'Mẫu in' }))
    await userEvent.click(screen.getByRole('option', { name: 'Mẫu thuế' }))
    expect(onTemplateChange).toHaveBeenCalledWith('tax')
    expect(onLayoutChange).not.toHaveBeenCalled()
  })

  it('on the supplier page the common group leads back with the same template', async () => {
    const { onTemplateChange, onLayoutChange } = renderOptions({
      layout: 'supplier',
      template: 'normal-unsigned',
      supplierLayout: { enabled: true },
    })
    expect(screen.getByRole('combobox', { name: 'Mẫu in' })).toHaveTextContent(
      'Theo NCC · Mẫu thường – không chữ ký',
    )
    await userEvent.click(screen.getByRole('combobox', { name: 'Mẫu in' }))
    await userEvent.click(screen.getByRole('option', { name: 'Mẫu thường – không chữ ký' }))
    expect(onLayoutChange).toHaveBeenCalledWith('common', 'normal-unsigned')
    expect(onTemplateChange).not.toHaveBeenCalled()
  })

  it('without chosen-supplier lines the supplier group is greyed out with the reason', async () => {
    const { onLayoutChange } = renderOptions({ supplierLayout: { enabled: false } })
    await userEvent.click(screen.getByRole('combobox', { name: 'Mẫu in' }))
    expect(screen.getByText(/chưa có dòng chốt nhà cung cấp/)).toBeInTheDocument()
    const supplierOptions = screen.getAllByRole('option', { name: /Theo NCC/ })
    expect(supplierOptions).toHaveLength(3)
    for (const option of supplierOptions) expect(option).toHaveAttribute('aria-disabled', 'true')
    expect(onLayoutChange).not.toHaveBeenCalled()
  })
})
