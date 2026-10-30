import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ReportPrLinesTab } from './report-pr-lines-tab'
import { splitPoCodes, type PrLineRow } from '../types/purchase-report'

//  Chặn ở tầng HOOK để bắt nguyên BỘ THAM SỐ bảng gửi đi (`line_status` nối
//  dấu phẩy, trang về 1…) — tham số chỉ hiện nguyên vẹn ở đầu vào của hook.
const listCalls: Record<string, unknown>[] = []
let rows: PrLineRow[] = []

vi.mock('../hooks/use-purchase-report', () => ({
  usePrLines: (params: Record<string, unknown>) => {
    listCalls.push(params)
    return {
      data: { items: rows, total: rows.length, page: 1, page_size: 20, assignees: [] },
      isLoading: false,
      isError: false,
    }
  },
}))

let canReadSupplier = true
let canExportReport = true
let canReadPurchaseOrder = true

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => {
      if (entity === 'supplier' && action === 'read') return canReadSupplier
      if (entity === 'report' && action === 'export') return canExportReport
      if (entity === 'purchase_order' && action === 'read') return canReadPurchaseOrder
      return true
    },
    canAccess: () => true,
  }),
}))

const downloadFile = vi.fn()

vi.mock('@/core/api', async (importOriginal) => ({
  ...(await importOriginal<Record<string, unknown>>()),
  downloadFile: (...args: unknown[]) => downloadFile(...args),
}))

const toastError = vi.fn()

vi.mock('sonner', () => ({
  toast: { error: (...args: unknown[]) => toastError(...args), success: vi.fn() },
}))

const BASE_ROW: PrLineRow = {
  id: 11,
  pr_id: 5,
  pr_code: 'PYC-0005',
  created_date: '2026-10-01',
  requester: 'Nguyễn Văn A',
  department: 'Phòng Sản xuất',
  product_code: 'SP-01',
  product_name: 'Thùng carton 3 lớp',
  warehouse: 'Kho tổng',
  item_group: 'Bao bì',
  gram: '',
  qty: 100,
  price: 1000,
  vat_pct: 8,
  amount: 100000,
  status: 'approved',
  line_status: 'ordered',
  expected_date: '',
  assignee: 'NSU001',
  assignee_name: 'Trần Thị B',
}

const FULL_ROW: PrLineRow = {
  ...BASE_ROW,
  qty_ordered: 60,
  qty_received: 25,
  //  Khoảng trắng thừa + mục rỗng + mã lặp: đúng dạng máy chủ có thể nối ra
  //  khi một dòng giao nhiều lần vào cùng một đơn.
  po_codes: ' PO-0001, PO-0002,,PO-0001 ',
  po_count: 2,
  suggested_supplier: 'NCC Bao bì Miền Tây',
  latest_po_supplier: 'NCC Giấy Cần Thơ',
}

//  Máy chủ BẢN CŨ: mười chín trường mới vắng hẳn — màn không được nổ, ô in "—".
const OLD_SERVER_ROW: PrLineRow = { ...BASE_ROW, id: 12, product_name: 'Băng keo trong' }

function build() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ReportPrLinesTab year="2026" companyId="7" />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function lastCall() {
  return listCalls[listCalls.length - 1]
}

beforeEach(() => {
  listCalls.length = 0
  rows = [FULL_ROW]
  localStorage.clear()
  downloadFile.mockReset()
  toastError.mockReset()
  canReadSupplier = true
  canExportReport = true
  canReadPurchaseOrder = true
})

describe('splitPoCodes', () => {
  it('trims, drops empty parts and de-duplicates the comma-joined codes', () => {
    expect(splitPoCodes(' PO-1, PO-2,,PO-1 ')).toEqual(['PO-1', 'PO-2'])
  })

  it('returns nothing for null, undefined, empty and comma-only strings', () => {
    expect(splitPoCodes(null)).toEqual([])
    expect(splitPoCodes(undefined)).toEqual([])
    expect(splitPoCodes('')).toEqual([])
    expect(splitPoCodes(' , ,')).toEqual([])
  })
})

describe('ReportPrLinesTab — cột mới (bao-CR-691)', () => {
  it('shows ordered / received quantity and PO codes by default, keeps the rest hidden', () => {
    build()

    expect(screen.getByRole('columnheader', { name: /SL đã đặt/ })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: /SL đã nhận/ })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: /Mã ĐMH/ })).toBeInTheDocument()
    expect(screen.getByText('60')).toBeInTheDocument()
    expect(screen.getByText('25')).toBeInTheDocument()

    //  Mười sáu cột còn lại chỉ bật ở menu Cột.
    expect(screen.queryByRole('columnheader', { name: /Mục đích/ })).toBeNull()
    expect(screen.queryByRole('columnheader', { name: /Ghi chú dòng/ })).toBeNull()
    expect(screen.queryByRole('columnheader', { name: /NCC đề xuất/ })).toBeNull()
  })

  it('links every distinct PO code to the PO list searched by that code', () => {
    build()

    const links = screen.getAllByRole('link', { name: /^PO-000/ })
    expect(links.map((link) => link.textContent)).toEqual(['PO-0001', 'PO-0002'])
    expect(links[0]).toHaveAttribute('href', '/procurement/purchase-orders?q=PO-0001')
    expect(links[1]).toHaveAttribute('href', '/procurement/purchase-orders?q=PO-0002')
  })

  it('prints PO codes as plain text when the viewer cannot read purchase orders', () => {
    canReadPurchaseOrder = false
    build()

    expect(screen.queryByRole('link', { name: /^PO-000/ })).toBeNull()
    expect(screen.getByText('PO-0001')).toBeInTheDocument()
  })

  it('names the two status columns after their owner, line progress first', () => {
    //  Đại ca chốt 28/10: "Tiến độ" / "Trạng thái" trần làm người đọc lẫn tiến
    //  độ của DÒNG với trạng thái của PHIẾU.
    build()

    const headers = screen.getAllByRole('columnheader').map((cell) => cell.textContent ?? '')
    const lineIndex = headers.findIndex((text) => text.includes('Tiến độ dòng'))
    const prIndex = headers.findIndex((text) => text.includes('Trạng thái phiếu'))
    expect(lineIndex).toBeGreaterThanOrEqual(0)
    expect(prIndex).toBeGreaterThan(lineIndex)
    expect(headers.some((text) => text.trim() === 'Tiến độ' || text.trim() === 'Trạng thái')).toBe(
      false,
    )
    expect(screen.getByRole('button', { name: /Tất cả tiến độ dòng/ })).toBeInTheDocument()
    const comboboxTexts = screen.getAllByRole('combobox').map((box) => box.textContent ?? '')
    expect(comboboxTexts.some((text) => /trạng thái phiếu/i.test(text))).toBe(true)
  })

  it('survives a server that does not send the new fields yet', () => {
    rows = [OLD_SERVER_ROW]
    build()

    const row = screen.getByText('Băng keo trong').closest('tr')
    if (!row) throw new Error('không thấy dòng của máy chủ bản cũ')
    //  Ba cột mới đang hiện đều in "—", không in "0" hay "undefined".
    expect(within(row).getAllByText('—').length).toBeGreaterThanOrEqual(3)
    expect(row.textContent).not.toContain('undefined')
    expect(row.textContent).not.toContain('null')
  })
})

describe('ReportPrLinesTab — cột NCC theo quyền', () => {
  async function openColumnMenu() {
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /Cột/ }))
    return (await screen.findAllByTitle('Ẩn / hiện cột')).map((item) => item.textContent ?? '')
  }

  it('offers both supplier columns in the column menu to a viewer with supplier.read', async () => {
    build()

    const entries = await openColumnMenu()
    expect(entries.some((text) => text.includes('NCC đề xuất'))).toBe(true)
    expect(entries.some((text) => text.includes('NCC đơn gần nhất'))).toBe(true)
  })

  it('drops the supplier columns entirely, not even in the column menu, without supplier.read', async () => {
    canReadSupplier = false
    build()

    const entries = await openColumnMenu()
    expect(entries.some((text) => text.includes('NCC đề xuất'))).toBe(false)
    expect(entries.some((text) => text.includes('NCC đơn gần nhất'))).toBe(false)
    //  Cột không-NCC ẩn mặc định vẫn còn trong menu — chỉ hai cột NCC bị rút.
    expect(entries.some((text) => text.includes('Mục đích'))).toBe(true)
  })

  it('keeps a stored layout from resurrecting the supplier columns after losing supplier.read', async () => {
    //  Người từng bật cột NCC (bố cục nhớ ở localStorage) rồi bị thu quyền: bản
    //  lưu không được kéo cột đó trở lại bảng.
    const user = userEvent.setup()
    const first = build()
    await user.click(screen.getByRole('button', { name: /Cột/ }))
    const toggle = (await screen.findAllByTitle('Ẩn / hiện cột')).find((item) =>
      item.textContent?.includes('NCC đề xuất'),
    )
    if (!toggle) throw new Error('menu Cột không có mục NCC đề xuất')
    await user.click(toggle)
    //  Menu Radix đang mở thì phần còn lại của trang bị `aria-hidden` — đóng
    //  menu trước rồi mới tìm tiêu đề cột theo vai trò.
    await user.keyboard('{Escape}')
    await waitFor(() =>
      expect(screen.getByRole('columnheader', { name: /NCC đề xuất/ })).toBeInTheDocument(),
    )
    first.unmount()

    canReadSupplier = false
    build()

    expect(screen.queryByRole('columnheader', { name: /NCC/ })).toBeNull()
    expect(screen.queryByText('NCC Bao bì Miền Tây')).toBeNull()
  })
})

describe('ReportPrLinesTab — lọc nhiều tiến độ', () => {
  it('sends no line_status while nothing is picked — empty means all', () => {
    build()

    expect(lastCall().line_status).toBeUndefined()
  })

  it('joins several picked progress values with a comma and goes back to page 1', async () => {
    const user = userEvent.setup()
    build()

    await user.click(screen.getByRole('button', { name: /Tất cả tiến độ dòng/ }))
    await user.click(screen.getByRole('button', { name: /Chưa được đặt hàng \(gộp\)/ }))
    await user.click(screen.getByRole('button', { name: /^Đã đặt hàng$/ }))

    await waitFor(() => expect(lastCall().line_status).toBe('chua_dat,ordered'))
    expect(lastCall().page).toBe(1)
  })
})

describe('ReportPrLinesTab — Xuất Excel', () => {
  it('hides the export button without report.export', () => {
    canExportReport = false
    build()

    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).toBeNull()
  })

  it('exports with the filters on screen but without the paging', async () => {
    //  Gửi kèm `page`/`page_size` thì tệp chỉ có đúng trang đang xem.
    const user = userEvent.setup()
    build()

    await user.click(screen.getByRole('button', { name: /Tất cả tiến độ dòng/ }))
    await user.click(screen.getByRole('button', { name: /^Chưa tạo đơn mua hàng$/ }))
    await user.click(screen.getByRole('button', { name: /^Chưa đặt hàng$/ }))
    await user.keyboard('{Escape}')
    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))

    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
    const [url] = downloadFile.mock.calls[0] as [string, string]
    const parsed = new URL(url, 'http://x')
    expect(parsed.pathname).toBe('/api/reports/pr-lines/export')
    expect(parsed.searchParams.get('year')).toBe('2026')
    expect(parsed.searchParams.get('company_id')).toBe('7')
    expect(parsed.searchParams.get('line_status')).toBe('no_po,not_ordered')
    expect(parsed.searchParams.has('page')).toBe(false)
    expect(parsed.searchParams.has('page_size')).toBe(false)
  })

  it('shows the server reason when the export is refused, not a generic error', async () => {
    //  Quá 5.000 dòng máy chủ trả 400; tải bằng `responseType: 'blob'` nên câu
    //  lỗi về dạng blob — không đọc lại thì người dùng chỉ thấy "có lỗi xảy ra".
    const body = JSON.stringify({
      success: false,
      error: { code: 'TOO_MANY_ROWS', message: 'Quá 5.000 dòng, hãy lọc hẹp lại' },
    })
    downloadFile.mockRejectedValue({ response: { status: 400, data: new Blob([body]) } })
    const user = userEvent.setup()
    build()

    await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))

    await waitFor(() => expect(toastError).toHaveBeenCalledWith('Quá 5.000 dòng, hãy lọc hẹp lại'))
    //  Lỗi xong nút phải bấm lại được, không kẹt ở trạng thái đang xuất.
    expect(screen.getByRole('button', { name: /Xuất Excel/ })).toBeEnabled()
  })

  it('fires one download for a double click', async () => {
    let finish: () => void = () => {}
    downloadFile.mockImplementation(() => new Promise<void>((resolve) => (finish = resolve)))
    const user = userEvent.setup()
    build()

    await user.dblClick(screen.getByRole('button', { name: /Xuất Excel/ }))
    finish()

    await waitFor(() => expect(downloadFile).toHaveBeenCalledTimes(1))
  })
})
