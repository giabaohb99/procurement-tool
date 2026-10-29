import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { createSelectionColumn } from './selection-column'
import { DataTable } from './data-table'
import { RowLink } from './row-link'
import { isInteractiveTarget, toAppHref, wantsNewTab } from './row-new-tab'
import type { DataTableColumn } from './types'

//  bao-CR-693 (phiếu TK29102601): người dùng lọc danh sách đơn mua hàng rồi
//  muốn mở NHIỀU đơn cùng lúc mà không mất trang đang lọc. Ctrl / Cmd + bấm và
//  chuột giữa phải mở TAB MỚI; bấm thường giữ y như cũ (cùng tab).

interface Row {
  id: number
  code: string
  name: string
}

const ROWS: Row[] = [
  { id: 7, code: 'PO-0007', name: 'Đơn bảy' },
  { id: 8, code: 'PO-0008', name: 'Đơn tám' },
]

const DETAIL = (id: number) => `/procurement/purchase-orders/${id}`

function renderTable({
  withHref = true,
  columns,
}: { withHref?: boolean; columns?: DataTableColumn<Row>[] } = {}) {
  const onRowClick = vi.fn()
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const cols: DataTableColumn<Row>[] = columns ?? [
    { key: 'code', header: 'Mã', cell: (r) => <RowLink to={DETAIL(r.id)}>{r.code}</RowLink> },
    { key: 'name', header: 'Tên', cell: (r) => r.name },
  ]
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/procurement/purchase-orders?status=draft']}>
        <Routes>
          <Route
            path="/procurement/purchase-orders"
            element={
              <DataTable
                columns={cols}
                rows={ROWS}
                getRowId={(r) => r.id}
                idColumn={false}
                onRowClick={onRowClick}
                getRowHref={withHref ? (r) => DETAIL(r.id) : undefined}
              />
            }
          />
          <Route path="/procurement/purchase-orders/:id" element={<p>Trang chi tiết đơn</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return { onRowClick }
}

function middleClick(el: Element) {
  fireEvent.mouseDown(el, { button: 1 })
  fireEvent(el, new MouseEvent('auxclick', { bubbles: true, cancelable: true, button: 1 }))
}

let openSpy: ReturnType<typeof vi.spyOn>

beforeEach(() => {
  localStorage.clear()
  openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)
})

afterEach(() => {
  openSpy.mockRestore()
})

describe('DataTable getRowHref — mở chi tiết ở tab mới', () => {
  it('Ctrl + click on a row opens the detail in a new tab and leaves the filtered list in place', () => {
    const { onRowClick } = renderTable()

    fireEvent.click(screen.getByText('Đơn bảy'), { ctrlKey: true })

    expect(openSpy).toHaveBeenCalledTimes(1)
    expect(openSpy).toHaveBeenCalledWith('/procurement/purchase-orders/7', '_blank', 'noopener')
    expect(onRowClick).not.toHaveBeenCalled()
    expect(screen.queryByText('Trang chi tiết đơn')).not.toBeInTheDocument()
  })

  it('Cmd + click (macOS) behaves like Ctrl + click', () => {
    const { onRowClick } = renderTable()

    fireEvent.click(screen.getByText('Đơn tám'), { metaKey: true })

    expect(openSpy).toHaveBeenCalledWith('/procurement/purchase-orders/8', '_blank', 'noopener')
    expect(onRowClick).not.toHaveBeenCalled()
  })

  it('middle click on a row opens a new tab exactly once and blocks Windows autoscroll', () => {
    const { onRowClick } = renderTable()
    const cell = screen.getByText('Đơn bảy')

    //  `mousedown` chuột giữa bị chặn — không chặn thì Windows bật cuộn tự động
    //  và trình duyệt không bắn `auxclick`, bấm chuột giữa thành vô tác dụng.
    expect(fireEvent.mouseDown(cell, { button: 1 })).toBe(false)
    fireEvent(cell, new MouseEvent('auxclick', { bubbles: true, cancelable: true, button: 1 }))

    expect(openSpy).toHaveBeenCalledTimes(1)
    expect(openSpy).toHaveBeenCalledWith('/procurement/purchase-orders/7', '_blank', 'noopener')
    expect(onRowClick).not.toHaveBeenCalled()
  })

  it('right click (auxclick button 2) does not open anything', () => {
    renderTable()
    fireEvent(
      screen.getByText('Đơn bảy'),
      new MouseEvent('auxclick', { bubbles: true, cancelable: true, button: 2 }),
    )
    expect(openSpy).not.toHaveBeenCalled()
  })

  it('plain click keeps the old behaviour: onRowClick, no new tab', () => {
    const { onRowClick } = renderTable()

    fireEvent.click(screen.getByText('Đơn bảy'))

    expect(onRowClick).toHaveBeenCalledTimes(1)
    expect(onRowClick).toHaveBeenCalledWith(ROWS[0])
    expect(openSpy).not.toHaveBeenCalled()
  })

  it('without getRowHref, Ctrl + click still runs onRowClick as before (other screens unchanged)', () => {
    const { onRowClick } = renderTable({ withHref: false })
    const cell = screen.getByText('Đơn bảy')

    fireEvent.click(cell, { ctrlKey: true })
    middleClick(cell)

    expect(onRowClick).toHaveBeenCalledTimes(1)
    expect(openSpy).not.toHaveBeenCalled()
  })

  it('getRowHref returning undefined opens nothing on Ctrl + click', () => {
    const onRowClick = vi.fn()
    const client = new QueryClient()
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <DataTable
            columns={[{ key: 'name', header: 'Tên', cell: (r: Row) => r.name }]}
            rows={ROWS}
            getRowId={(r) => r.id}
            idColumn={false}
            onRowClick={onRowClick}
            getRowHref={() => undefined}
          />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    fireEvent.click(screen.getByText('Đơn bảy'), { ctrlKey: true })
    middleClick(screen.getByText('Đơn tám'))
    expect(openSpy).not.toHaveBeenCalled()
    expect(onRowClick).not.toHaveBeenCalled()
  })

  it('Ctrl + click or middle click on the selection checkbox never opens a tab', () => {
    const selection = createSelectionColumn<Row>({
      getRowId: (r) => r.id,
      selectedIds: new Set<number>(),
      onToggleRow: () => {},
      onToggleAllOnPage: () => {},
      allOnPageSelected: false,
      someOnPageSelected: false,
    })
    const { onRowClick } = renderTable({
      columns: [selection, { key: 'name', header: 'Tên', cell: (r) => r.name }],
    })
    const box = screen.getAllByRole('checkbox')[1]

    fireEvent.click(box, { ctrlKey: true })
    middleClick(box)

    expect(openSpy).not.toHaveBeenCalled()
    expect(onRowClick).not.toHaveBeenCalled()
  })
})

describe('RowLink — mã chứng từ là link thật', () => {
  it('renders a real <a href> so the browser context menu offers "Open in new tab"', () => {
    renderTable()
    const link = screen.getByRole('link', { name: 'PO-0007' })
    expect(link).toHaveAttribute('href', '/procurement/purchase-orders/7')
  })

  it('plain click navigates inside the SPA exactly once and does not trigger the row', () => {
    const { onRowClick } = renderTable()

    fireEvent.click(screen.getByRole('link', { name: 'PO-0007' }))

    expect(screen.getByText('Trang chi tiết đơn')).toBeInTheDocument()
    expect(onRowClick).not.toHaveBeenCalled()
    expect(openSpy).not.toHaveBeenCalled()
  })

  it('Ctrl + click and middle click are left to the browser — the row does not open a second tab', () => {
    const { onRowClick } = renderTable()
    const link = screen.getByRole('link', { name: 'PO-0007' })

    //  Không bị preventDefault: trình duyệt tự mở link ở tab mới.
    expect(fireEvent.click(link, { ctrlKey: true })).toBe(true)
    expect(fireEvent.mouseDown(link, { button: 1 })).toBe(true)
    fireEvent(link, new MouseEvent('auxclick', { bubbles: true, cancelable: true, button: 1 }))

    expect(openSpy).not.toHaveBeenCalled()
    expect(onRowClick).not.toHaveBeenCalled()
    expect(screen.queryByText('Trang chi tiết đơn')).not.toBeInTheDocument()
  })
})

describe('row-new-tab helpers', () => {
  it('wantsNewTab: only Ctrl, Cmd or the middle button count', () => {
    expect(wantsNewTab({ ctrlKey: true, metaKey: false, button: 0 })).toBe(true)
    expect(wantsNewTab({ ctrlKey: false, metaKey: true, button: 0 })).toBe(true)
    expect(wantsNewTab({ ctrlKey: false, metaKey: false, button: 1 })).toBe(true)
    expect(wantsNewTab({ ctrlKey: false, metaKey: false, button: 0 })).toBe(false)
    expect(wantsNewTab({ ctrlKey: false, metaKey: false, button: 2 })).toBe(false)
  })

  it('isInteractiveTarget: nested inside a button counts, plain text and non-elements do not', () => {
    const button = document.createElement('button')
    const icon = document.createElement('span')
    button.appendChild(icon)
    const text = document.createElement('span')
    expect(isInteractiveTarget({ target: icon })).toBe(true)
    expect(isInteractiveTarget({ target: text })).toBe(false)
    expect(isInteractiveTarget({ target: null })).toBe(false)
    expect(isInteractiveTarget({ target: document.createTextNode('x') })).toBe(false)
  })

  it('toAppHref: keeps router paths absolute and leaves full URLs alone', () => {
    expect(toAppHref('/procurement/purchase-orders/7')).toBe('/procurement/purchase-orders/7')
    expect(toAppHref('procurement/purchase-orders/7')).toBe('/procurement/purchase-orders/7')
    expect(toAppHref('https://erp.example/x')).toBe('https://erp.example/x')
  })
})
