import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { McpCall } from '../types/ai-skill'
import { CallLogPage } from './call-log-page'

/**
 * Cột "Số ký tự kết quả" của Nhật ký lượt gọi (ai-CR-228). Chỗ dễ lủng: in "0" cho lượt không đo (initialize /
 * tools/list / dòng cũ) làm người đọc tưởng công cụ trả rỗng; số lớn không có dấu chấm nghìn khó đọc; máy chủ cũ
 * chưa có trường thì ô in "undefined" hoặc "NaN"; cột không ẩn được qua menu Cột như các cột khác.
 *
 * Ô "không đo": hàm định dạng trả "—" như mọi cột khác của màn, rồi `DataTable` theo luật CR-132 đổi "—" thành ô
 * TRỐNG (cùng cách cột Người / Ứng dụng AI / IP đang hiện). Bài kiểm khẳng định ô trống để ai đổi luật đó thấy ngay.
 */
const EMPTY_CELL = /^$/

const apiGet = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
//  Giữ buildCsv thật, chỉ chặn tải tệp để đọc lại nội dung CSV
const downloadCsv = vi.fn()
vi.mock('../utils/csv-export', async (importOriginal) => ({
  ...(await importOriginal<Record<string, unknown>>()),
  downloadCsv: (...args: unknown[]) => downloadCsv(...args),
}))

function call(id: number, over: Partial<McpCall> = {}): McpCall {
  return {
    id,
    created_at: '2026-10-19T10:00:00',
    key_id: 1,
    user_id: 7,
    employee_id: 7,
    department_id: 0,
    company_id: 0,
    client_name: 'Claude',
    method: 'tools/call',
    tool: `tool_${id}`,
    skill_id: 0,
    status: 1,
    status_label: 'Thành công',
    deny_reason: '',
    duration_ms: 120,
    ip: '1.2.3.4',
    user_label: 'Nguyễn Văn A',
    result_chars: 0,
    ...over,
  }
}

function mockServer(items: McpCall[]) {
  apiGet.mockImplementation((url: string) => {
    if (url.endsWith('/mcp-calls')) return Promise.resolve({ items, total: items.length, page: 1, size: 20, statuses: [] })
    return Promise.resolve({ items: [] })
  })
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <CallLogPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Ô "Số ký tự kết quả" của dòng có công cụ `tool` — tìm theo vị trí cột ở hàng tiêu đề, khỏi phụ thuộc thứ tự cột. */
function resultCellOf(tool: string): HTMLElement {
  const headers = screen.getAllByRole('columnheader')
  const index = headers.findIndex((h) => h.textContent?.includes('Số ký tự kết quả'))
  expect(index).toBeGreaterThanOrEqual(0)
  const row = screen.getByText(tool).closest('tr')
  if (!row) throw new Error(`không thấy dòng ${tool}`)
  return within(row).getAllByRole('cell')[index]
}

describe('CallLogPage — result size column (ai-CR-228)', () => {
  beforeEach(() => {
    apiGet.mockReset()
    localStorage.clear()
    useAuthStore.setState({ user: { id: 1, permissions: { ai_skill: { read: true } } } as never })
  })

  it('leaves 0 as an empty cell (never "0") and uses Vietnamese thousand separators for large values', async () => {
    mockServer([
      call(1, { tool: 'list_skills', result_chars: 0 }),
      call(2, { tool: 'read_skill', result_chars: 1234567 }),
      call(3, { tool: 'search_docs', result_chars: 999 }),
    ])
    renderPage()

    await screen.findByText('read_skill')
    expect(resultCellOf('list_skills')).toHaveTextContent(EMPTY_CELL)
    expect(resultCellOf('read_skill')).toHaveTextContent(/^1\.234\.567$/)
    expect(resultCellOf('search_docs')).toHaveTextContent(/^999$/)
  })

  it('stays empty, not "undefined" / "NaN", when an older server omits the field', async () => {
    const legacy = call(4, { tool: 'old_tool' })
    delete legacy.result_chars
    mockServer([legacy])
    renderPage()

    await screen.findByText('old_tool')
    expect(resultCellOf('old_tool')).toHaveTextContent(EMPTY_CELL)
  })

  it('can be hidden from the column menu like the other columns', async () => {
    const user = userEvent.setup()
    mockServer([call(5, { tool: 'read_skill', result_chars: 2500 })])
    renderPage()

    await screen.findByText('2.500')
    await user.click(screen.getByRole('button', { name: /Cột/ }))
    const toggle = (await screen.findAllByTitle('Ẩn / hiện cột')).find((b) => b.textContent?.includes('Số ký tự kết quả'))
    if (!toggle) throw new Error('menu Cột không có mục Số ký tự kết quả')
    expect(toggle).toBeEnabled()
    await user.click(toggle)

    expect(screen.queryByRole('columnheader', { name: /Số ký tự kết quả/ })).not.toBeInTheDocument()
    expect(screen.queryByText('2.500')).not.toBeInTheDocument()
  })

  it('exports the size into the CSV, leaving unmeasured calls blank instead of 0', async () => {
    const user = userEvent.setup()
    downloadCsv.mockReset()
    mockServer([call(6, { tool: 'read_skill', result_chars: 2500 }), call(7, { tool: 'list_skills', result_chars: 0 })])
    renderPage()

    await screen.findByText('2.500')
    await user.click(screen.getByRole('button', { name: /Xuất CSV/ }))
    expect(downloadCsv).toHaveBeenCalledTimes(1)
    const lines = String(downloadCsv.mock.calls[0][1]).replace(/^\uFEFF/, '').trim().split(/\r?\n/)
    //  Ô trong bài này không có dấu phẩy — tách thẳng rồi bỏ cặp nháy bao ngoài (nếu có)
    const cells = (line: string) => line.split(',').map((c) => c.replace(/^"|"$/g, ''))
    const col = cells(lines[0]).indexOf('Số ký tự kết quả')
    expect(col).toBeGreaterThanOrEqual(0)
    expect(cells(lines[1])[col]).toBe('2500')
    expect(cells(lines[2])[col]).toBe('')
  })
})

describe('CallLogPage — quick search and document column (bao-CR-696)', () => {
  beforeEach(() => {
    apiGet.mockReset()
    localStorage.clear()
    useAuthStore.setState({ user: { id: 1, permissions: { ai_skill: { read: true } } } as never })
  })

  /** Ô "Chứng từ" của dòng có công cụ `tool`. */
  function documentCellOf(tool: string): HTMLElement {
    const headers = screen.getAllByRole('columnheader')
    const index = headers.findIndex((h) => h.textContent?.includes('Chứng từ'))
    expect(index).toBeGreaterThanOrEqual(0)
    const row = screen.getByText(tool).closest('tr')
    if (!row) throw new Error(`không thấy dòng ${tool}`)
    return within(row).getAllByRole('cell')[index]
  }

  it('shows the document code, links it only inside the app, and a real dash when there is none', async () => {
    mockServer([
      call(1, { tool: 'propose_approval', doc_code: 'YCMH-2026-0012', doc_url: '/procurement/purchase-requests/12' }),
      call(2, { tool: 'draft_purchase_request', doc_code: 'YCMH-2026-0013', doc_url: '//evil.example/x' }),
      call(3, { tool: 'read_skill', doc_code: null, doc_url: null }),
      call(4, { tool: 'old_server_tool' }),
    ])
    renderPage()

    await screen.findByText('propose_approval')
    const link = within(documentCellOf('propose_approval')).getByRole('link', { name: 'YCMH-2026-0012' })
    expect(link).toHaveAttribute('href', '/procurement/purchase-requests/12')
    //  Link ra ngoài bị bỏ, mã vẫn hiện để đối chiếu.
    expect(within(documentCellOf('draft_purchase_request')).queryByRole('link')).not.toBeInTheDocument()
    expect(documentCellOf('draft_purchase_request')).toHaveTextContent(/^YCMH-2026-0013$/)
    //  Gạch ngang thật (bọc <span>) — không phải ô trống, không phải chữ "null" / "undefined".
    expect(documentCellOf('read_skill')).toHaveTextContent(/^—$/)
    expect(documentCellOf('old_server_tool')).toHaveTextContent(/^—$/)
  })

  it('exports the document code into the CSV, blank for calls without one', async () => {
    const user = userEvent.setup()
    downloadCsv.mockReset()
    mockServer([call(6, { tool: 'propose_approval', doc_code: 'DMH-01' }), call(7, { tool: 'read_skill' })])
    renderPage()

    await screen.findByText('DMH-01')
    await user.click(screen.getByRole('button', { name: /Xuất CSV/ }))
    const lines = String(downloadCsv.mock.calls[0][1]).replace(/^\uFEFF/, '').trim().split(/\r?\n/)
    const cells = (line: string) => line.split(',').map((c) => c.replace(/^"|"$/g, ''))
    const col = cells(lines[0]).indexOf('Chứng từ')
    expect(col).toBeGreaterThanOrEqual(0)
    expect(cells(lines[1])[col]).toBe('DMH-01')
    expect(cells(lines[2])[col]).toBe('')
  })

  it('sends one keyword as q for both person and tool, and drops the old tool parameter', async () => {
    const user = userEvent.setup()
    mockServer([call(8, { tool: 'read_skill' })])
    renderPage()

    await screen.findByText('read_skill')
    await user.type(screen.getByRole('textbox', { name: 'Tìm theo người hoặc công cụ' }), 'Nguyễn')
    await waitFor(() =>
      expect(apiGet).toHaveBeenCalledWith('/api/agent-hub/mcp-calls', {
        params: expect.objectContaining({ q: 'Nguyễn', page: 1 }),
      }),
    )
    const sent = apiGet.mock.calls.filter(([u]) => u === '/api/agent-hub/mcp-calls').map(([, cfg]) => cfg.params)
    expect(sent.every((p) => !('tool' in p))).toBe(true)
    //  Ô trống thì không gửi `q=` rỗng (máy chủ coi tham số rỗng là lỗi kiểu).
    expect('q' in sent[0]).toBe(false)
  })
})
