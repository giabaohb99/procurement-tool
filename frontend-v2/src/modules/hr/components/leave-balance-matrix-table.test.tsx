import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { LeaveBalanceMatrix } from '../api/leave-balance-matrix-api'
import { LeaveBalanceMatrixTable } from './leave-balance-matrix-table'

const apiGet = vi.fn()
const downloadFile = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  downloadFile: (...a: unknown[]) => downloadFile(...a),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  extractErrorMessage: () => 'lỗi',
  httpClient: {},
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() } }))

let granted = new Set<string>()
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.has(`${entity}.${action}`) }),
}))

const MATRIX: LeaveBalanceMatrix = {
  year: 2026,
  columns: [
    { leave_type_id: 3, name: 'Phép năm' },
    { leave_type_id: 7, name: 'Nghỉ bù' },
  ],
  items: [
    //  Khóa `cells` là CHUỖI như backend trả; người thứ hai không có quỹ "Nghỉ bù" (vắng khóa "7").
    { employee_id: 11, code: 'NSU001', name: 'Trần An', department_name: 'Kế toán', cells: { '3': 12, '7': 0 }, total: 12 },
    { employee_id: 12, code: 'NSU002', name: 'Lê Bình', department_name: '', cells: { '3': -1.5 }, total: -1.5 },
  ],
  total: 2,
}

/** Màn cha giữ ô tìm `?q=` rồi truyền xuống (review L9) — dựng đúng như vậy. */
function Harness() {
  const search = useUrlSearchParam()
  return <LeaveBalanceMatrixTable year="2026" onYearChange={() => {}} search={search} />
}

function renderTable(url = '/hr/leave-balances?view=people') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <Harness />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Ô của một người ở cột có tiêu đề `header` — đi theo dòng chứa tên người đó. */
function cellOf(personName: string, header: string) {
  const headers = screen.getAllByRole('columnheader').map((h) => h.textContent?.trim())
  const index = headers.findIndex((h) => h?.startsWith(header))
  const row = screen.getByText(personName).closest('tr')
  if (!row || index < 0) throw new Error(`không thấy ô ${personName} × ${header}`)
  return within(row).getAllByRole('cell')[index]
}

beforeEach(() => {
  localStorage.clear()
  granted = new Set()
  apiGet.mockReset().mockImplementation((url: string) =>
    Promise.resolve(url === '/api/leave-balances/matrix' ? MATRIX : { items: [], total: 0 }),
  )
  downloadFile.mockReset().mockResolvedValue(undefined)
})

describe('LeaveBalanceMatrixTable (duoc-CR-717)', () => {
  it('builds one column per leave type the backend returned, plus a total column', async () => {
    renderTable()
    await screen.findByText('Trần An')
    const headers = screen.getAllByRole('columnheader').map((h) => h.textContent?.trim() ?? '')
    expect(headers.some((h) => h.startsWith('Phép năm'))).toBe(true)
    expect(headers.some((h) => h.startsWith('Nghỉ bù'))).toBe(true)
    expect(headers.some((h) => h.startsWith('Tổng còn lại'))).toBe(true)
    expect(apiGet).toHaveBeenCalledWith('/api/leave-balances/matrix', {
      params: expect.objectContaining({ year: 2026, page: 1 }),
    })
  })

  it('keeps "Tổng còn lại" as the LAST column even when a saved layout puts it elsewhere (review L8)', async () => {
    //  Bố cục lưu từ trước khi có cột "Nghỉ bù": cột loại nghỉ mới nối vào CUỐI thứ tự đã lưu — không ghim
    //  `stickyRight` thì "Tổng" bị đẩy vào giữa bảng.
    localStorage.setItem(
      'erp.table.hr.leave-balances.matrix',
      JSON.stringify({ columnOrder: ['total', 'code', 'name', 'department', 'lt-3'] }),
    )
    renderTable()
    await screen.findByText('Trần An')
    const headers = screen.getAllByRole('columnheader').map((h) => h.textContent?.trim() ?? '')
    expect(headers.at(-1)).toMatch(/^Tổng còn lại/)
  })

  it('reads cells by STRING key, shows "—" for a missing type and a real 0 for a used-up one', async () => {
    renderTable()
    await screen.findByText('Trần An')
    expect(cellOf('Trần An', 'Phép năm')).toHaveTextContent('12')
    expect(cellOf('Trần An', 'Nghỉ bù')).toHaveTextContent(/^0$/)
    expect(cellOf('Lê Bình', 'Nghỉ bù')).toHaveTextContent('—')
  })

  it('paints negative balances red (advance leave beyond the quota)', async () => {
    renderTable()
    await screen.findByText('Lê Bình')
    const negative = within(cellOf('Lê Bình', 'Phép năm')).getByText('-1.5')
    expect(negative).toHaveClass('text-destructive')
    expect(within(cellOf('Trần An', 'Phép năm')).getByText('12')).not.toHaveClass('text-destructive')
  })

  it('hides the Excel export without leave_balance.export', async () => {
    renderTable()
    await screen.findByText('Trần An')
    expect(screen.queryByRole('button', { name: /Xuất Excel/ })).not.toBeInTheDocument()
  })

  it('exports with the current filters but without paging, once per burst of clicks', async () => {
    granted = new Set(['leave_balance.export'])
    let finish: () => void = () => {}
    downloadFile.mockImplementation(() => new Promise<void>((resolve) => (finish = resolve)))
    const user = userEvent.setup()
    renderTable()
    await screen.findByText('Trần An')
    const button = screen.getByRole('button', { name: /Xuất Excel/ })
    await user.click(button)
    await user.click(button)
    expect(downloadFile).toHaveBeenCalledTimes(1)
    expect(downloadFile).toHaveBeenCalledWith(
      '/api/leave-balances/matrix/export',
      'quy-phep-theo-nhan-su-2026.xlsx',
      { year: 2026 },
    )
    finish()
    await waitFor(() => expect(button).toBeEnabled())
  })

  it('says "no match" rather than "nobody allocated" when a search is active', async () => {
    apiGet.mockImplementation((url: string) =>
      Promise.resolve(url === '/api/leave-balances/matrix' ? { ...MATRIX, items: [], total: 0 } : { items: [] }),
    )
    const user = userEvent.setup()
    renderTable()
    expect(await screen.findByText('Chưa có ai được cấp quỹ phép năm 2026.')).toBeInTheDocument()
    await user.type(screen.getByPlaceholderText('Tìm tên, mã nhân sự'), 'zzz')
    expect(await screen.findByText('Không có nhân sự nào khớp bộ lọc.')).toBeInTheDocument()
  })

  //  duoc-CR-748: ba cột đầu xếp tại MÁY CHỦ; cột số ngày tính bằng Python nên không xếp được.
  describe('sắp xếp cột (duoc-CR-748)', () => {
    const header = (text: string) => screen.getByText(text, { selector: 'thead span' })
    const lastParams = () => {
      const calls = apiGet.mock.calls.filter(([url]) => url === '/api/leave-balances/matrix')
      return (calls.at(-1)?.[1] as { params: Record<string, unknown> }).params
    }

    it('sends sort_by for Mã NV, Họ tên and Phòng ban (department_name) and goes back to page 1', async () => {
      const user = userEvent.setup()
      renderTable()
      await screen.findByText('Trần An')
      const cases: [string, string][] = [
        ['Mã NV', 'code'],
        ['Họ tên', 'name'],
        ['Phòng ban', 'department_name'],
      ]
      for (const [text, key] of cases) {
        await user.click(header(text))
        await waitFor(() => expect(lastParams()).toMatchObject({ sort_by: key, sort_dir: 'asc', page: 1 }))
      }
      await user.click(header('Phòng ban'))
      await waitFor(() => expect(lastParams()).toMatchObject({ sort_by: 'department_name', sort_dir: 'desc' }))
      await user.click(header('Phòng ban'))
      await waitFor(() => expect(lastParams().sort_by).toBeUndefined())
    })

    it('does NOT sort by Chính sách, a leave-type column or Tổng còn lại', async () => {
      const user = userEvent.setup()
      renderTable()
      await screen.findByText('Trần An')
      for (const text of ['Chính sách', 'Phép năm', 'Nghỉ bù', 'Tổng còn lại']) {
        await user.click(header(text))
      }
      expect(lastParams().sort_by).toBeUndefined()
    })

    it('exports in the SAME order the table is showing', async () => {
      granted = new Set(['leave_balance.export'])
      const user = userEvent.setup()
      renderTable('/hr/leave-balances?view=people&sort_by=name&sort_dir=desc')
      await screen.findByText('Trần An')
      await user.click(screen.getByRole('button', { name: /Xuất Excel/ }))
      expect(downloadFile).toHaveBeenCalledWith(
        '/api/leave-balances/matrix/export',
        'quy-phep-theo-nhan-su-2026.xlsx',
        { year: 2026, sort_by: 'name', sort_dir: 'desc' },
      )
    })
  })
})
