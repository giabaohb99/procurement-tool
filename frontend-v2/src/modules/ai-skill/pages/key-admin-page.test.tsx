import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import { confirm } from '@/shared/ui/confirm-dialog'
import type { AdminMcpKey, KeyAdminMeta } from '../types/ai-skill'
import { KeyAdminPage } from './key-admin-page'

/**
 * Màn "Kết nối" (G5, tên cũ Khóa nhân sự). Chỗ dễ lủng: tick chọn cả khóa đã thu hồi / hết hạn rồi bấm Thu hồi thì hộp xác nhận phải
 * nói đúng số khóa CÒN HIỆU LỰC và chỉ gửi những khóa đó; quyền xem / phát / thu hồi lấy từ `meta` của máy chủ.
 */

const apiGet = vi.fn()
const apiPost = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPatch: vi.fn(),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: vi.fn(() => Promise.resolve(true)) }))

const META: KeyAdminMeta = {
  days: [7, 30, 90], batch_max: 50, max_keys: 5,
  states: [{ value: 1, label: 'Chờ nhận' }, { value: 2, label: 'Đang dùng' }, { value: 3, label: 'Hết hạn' }, { value: 4, label: 'Đã thu hồi' }, { value: 5, label: 'Đang tắt' }],
  can_read: true, can_create: true, can_delete: true,
}

function key(id: number, state: number, owner: string): AdminMcpKey {
  return {
    id, name: `Khóa ${id}`, hint: `…${id}`, scope: 0, scope_label: 'chỉ đọc', expires_at: null, last_used_at: null,
    created_at: null, state, state_label: META.states[state - 1].label, issued_by: 1, claimed_at: null, batch_id: '',
    user_id: id + 100, owner_label: owner, department_id: 3, department: 'Thu mua', issued_by_label: 'Quản trị',
  }
}

function mockServer(meta: KeyAdminMeta, keys: AdminMcpKey[]) {
  apiGet.mockImplementation((url: string, config?: { params?: { client?: string } }) => {
    if (url.endsWith('/mcp-key-admin/meta')) return Promise.resolve(meta)
    if (url.endsWith('/mcp-key-admin/keys')) return Promise.resolve({ total: keys.length, page: 1, size: 20, has_more: false, items: keys })
    if (url.endsWith('/mcp-setup') && config?.params?.client) {
      return Promise.resolve({ client: 'cursor', label: 'Cursor', supported: true, auth: 'key', format: 'json',
        snippet: '{"key":"<KHÓA_CỦA_BẠN>"}', steps: ['Mở Cursor'], endpoint: 'https://erp.test/api/mcp', placeholder: '<KHÓA_CỦA_BẠN>' })
    }
    if (url.endsWith('/mcp-setup')) {
      return Promise.resolve({ endpoint: 'https://erp.test/api/mcp', placeholder: '<KHÓA_CỦA_BẠN>',
        clients: [{ client: 'cursor', label: 'Cursor', supported: true, auth: 'key' }] })
    }
    return Promise.resolve({ items: [] })
  })
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <KeyAdminPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset()
  apiPost.mockReset()
  vi.mocked(confirm).mockClear()
  useAuthStore.setState({ user: { id: 1, permissions: {} } as never })
})

describe('KeyAdminPage', () => {
  it('revokes only the live keys among the ticked rows and says that number', async () => {
    mockServer(META, [key(1, 2, 'An'), key(2, 4, 'Bình'), key(3, 1, 'Chi')])
    apiPost.mockResolvedValue({ revoked: 2 })
    renderPage()
    await userEvent.click(await screen.findByRole('checkbox', { name: /Chọn khóa Khóa 1 của An/ }))
    await userEvent.click(screen.getByRole('checkbox', { name: /Chọn khóa Khóa 2 của Bình/ }))
    await userEvent.click(screen.getByRole('checkbox', { name: /Chọn khóa Khóa 3 của Chi/ }))
    await userEvent.click(screen.getByRole('button', { name: /Thu hồi \(2\)/ }))
    expect(confirm).toHaveBeenCalledWith(expect.objectContaining({ confirmLabel: 'Thu hồi 2 khóa' }))
    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/mcp-key-admin/revoke', { key_ids: [1, 3] }),
    )
  })

  it('counts a switched-off key as live for revoking (tắt khác thu hồi)', async () => {
    mockServer(META, [key(5, 5, 'Đào'), key(2, 4, 'Bình')])
    apiPost.mockResolvedValue({ revoked: 1 })
    renderPage()
    await userEvent.click(await screen.findByRole('checkbox', { name: /Chọn khóa Khóa 5 của Đào/ }))
    await userEvent.click(screen.getByRole('checkbox', { name: /Chọn khóa Khóa 2 của Bình/ }))
    await userEvent.click(screen.getByRole('button', { name: /Thu hồi \(1\)/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/mcp-key-admin/revoke', { key_ids: [5] }))
  })

  it('shows the connection guide with the key placeholder only, and copies the public guide link', async () => {
    const writeText = vi.fn(() => Promise.resolve())
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
    mockServer(META, [key(1, 2, 'An')])
    renderPage()
    //  Cột phải (màn rộng) + nút mở hộp cùng nội dung (màn hẹp) — cả hai cùng có nhãn này.
    expect(await screen.findByRole('button', { name: 'Hướng dẫn kết nối' })).toBeInTheDocument()
    expect(await screen.findByText('{"key":"<KHÓA_CỦA_BẠN>"}')).toBeInTheDocument()
    expect(apiGet.mock.calls.some(([u]) => String(u).includes('/reveal') || String(u).endsWith('/mcp-keys'))).toBe(false)
    await userEvent.click(screen.getByRole('button', { name: 'Sao chép link hướng dẫn' }))
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(`${window.location.origin}/connect-ai`))
  })

  it('offers no revoke button when only dead keys are ticked', async () => {
    mockServer(META, [key(2, 4, 'Bình'), key(4, 3, 'Dũng')])
    renderPage()
    await userEvent.click(await screen.findByRole('checkbox', { name: /Chọn khóa Khóa 2 của Bình/ }))
    expect(screen.queryByRole('button', { name: /Thu hồi/ })).not.toBeInTheDocument()
  })

  it('hides tick boxes and the issue button from someone who may only read', async () => {
    mockServer({ ...META, can_create: false, can_delete: false }, [key(1, 2, 'An')])
    renderPage()
    expect(await screen.findByText('An')).toBeInTheDocument()
    expect(screen.queryByRole('checkbox', { name: /Chọn khóa/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Phát khóa/ })).not.toBeInTheDocument()
  })

  it('shows a clear refusal instead of an empty table when the server says no read right', async () => {
    mockServer({ ...META, can_read: false }, [])
    renderPage()
    expect(await screen.findByText('Không có quyền')).toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalledWith('/api/agent-hub/mcp-key-admin/keys', expect.anything())
  })
})

describe('KeyAdminPage as the Connections screen (bao-CR-696)', () => {
  function headerIndex(label: string): number {
    const index = screen.getAllByRole('columnheader').findIndex((h) => h.textContent?.trim() === label)
    expect(index, label).toBeGreaterThanOrEqual(0)
    return index
  }

  function cellOf(rowText: string, column: string): HTMLElement {
    const row = screen.getByText(rowText).closest('tr')
    if (!row) throw new Error(`không thấy dòng ${rowText}`)
    return within(row).getAllByRole('cell')[headerIndex(column)]
  }

  beforeEach(() => localStorage.clear())

  it('shows who, how, which app and where it returns to, from the proposed fields', async () => {
    mockServer(META, [
      {
        ...key(1, 2, 'An'),
        person_name: 'Nguyễn Văn An', employee_code: 'NSU001', email: 'an@dego.vn', dept_name: 'Kế toán',
        connection_type: 'oauth', app_name: 'ChatGPT', app_redirect_uri: 'https://chatgpt.com/connector/oauth/x',
      },
    ])
    renderPage()
    expect(await screen.findByText('Nguyễn Văn An')).toBeInTheDocument()
    expect(screen.getByText('NSU001 · an@dego.vn')).toBeInTheDocument()
    expect(cellOf('Nguyễn Văn An', 'Cách nối')).toHaveTextContent('OAuth')
    expect(cellOf('Nguyễn Văn An', 'Ứng dụng')).toHaveTextContent('ChatGPT')
    expect(cellOf('Nguyễn Văn An', 'Ứng dụng')).toHaveTextContent('chatgpt.com')
    expect(cellOf('Nguyễn Văn An', 'Phòng')).toHaveTextContent('Kế toán')
  })

  it('still fills every column from an older server, with a real dash for the unknown app', async () => {
    mockServer(META, [key(2, 2, 'Bình')])
    renderPage()
    expect(await screen.findByText('Bình')).toBeInTheDocument()
    expect(cellOf('Bình', 'Cách nối')).toHaveTextContent('Khóa riêng')
    expect(cellOf('Bình', 'Ứng dụng')).toHaveTextContent(/^—$/)
    expect(cellOf('Bình', 'Dùng lần cuối')).toHaveTextContent('Chưa dùng')
    expect(cellOf('Bình', 'Trạng thái')).toHaveTextContent('Đang dùng')
    expect(document.body.textContent).not.toMatch(/undefined|NaN/)
  })

  it('searches by name, email or employee code through the server, not before the user stops typing', async () => {
    const user = userEvent.setup()
    mockServer(META, [key(1, 2, 'An')])
    renderPage()
    await screen.findByText('An')
    await user.type(screen.getByRole('textbox', { name: 'Tìm theo tên, email, mã nhân viên' }), 'NSU001')
    await waitFor(() =>
      expect(apiGet).toHaveBeenCalledWith('/api/agent-hub/mcp-key-admin/keys', {
        params: expect.objectContaining({ q: 'NSU001', page: 1 }),
      }),
    )
    const sentQs = apiGet.mock.calls
      .filter(([u]) => u === '/api/agent-hub/mcp-key-admin/keys')
      .map(([, cfg]) => (cfg as { params: { q?: string } }).params.q)
    //  Hoãn gõ: không có lượt nào gửi từng mẩu dở dang "N", "NS"…
    expect(sentQs.filter((q) => q && q !== 'NSU001')).toEqual([])
  })

  it('tells an empty search apart from an empty system', async () => {
    const user = userEvent.setup()
    mockServer(META, [])
    renderPage()
    expect(await screen.findByText('Chưa có kết nối nào. Bấm Phát khóa để cấp cho một phòng.')).toBeInTheDocument()
    await user.type(screen.getByRole('textbox', { name: 'Tìm theo tên, email, mã nhân viên' }), 'không ai')
    expect(await screen.findByText('Không có kết nối nào khớp bộ lọc.')).toBeInTheDocument()
  })
})
