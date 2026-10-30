import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import { confirm } from '@/shared/ui/confirm-dialog'
import type { OAuthClient } from '../types/ai-skill'
import { OAuthClientsPage } from './oauth-clients-page'

/**
 * Màn "Ứng dụng AI đã kết nối" (bao-CR-635). Chỗ dễ lủng: tin tên tự khai (phải tô cảnh báo theo `trusted` của máy chủ,
 * không tự đoán); xóa mà không nói rõ số kết nối sẽ bị cắt; người thiếu quyền quản lý bot AI mở ra ăn 403 thay vì câu
 * giải thích; người chỉ đọc vẫn thấy nút Xóa.
 */

const apiGet = vi.fn()
const apiDelete = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiDelete: (...args: unknown[]) => apiDelete(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiPut: vi.fn(),
  httpClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: vi.fn(() => Promise.resolve(true)) }))

function client(id: number, over: Partial<OAuthClient> = {}): OAuthClient {
  return {
    id,
    client_id: `cid-${id}-abcdefghijklmnop`,
    client_name: `Ứng dụng ${id}`,
    redirect_hosts: ['chatgpt.com'],
    trusted: true,
    auth_method: 'none',
    ip: '1.2.3.4',
    created_at: '2026-10-19T10:00:00',
    last_used_at: null,
    live_grants: 0,
    ...over,
  }
}

function mockServer(items: OAuthClient[], canDelete = true) {
  apiGet.mockImplementation((url: string) => {
    if (url.endsWith('/oauth-clients')) return Promise.resolve({ items, can_delete: canDelete })
    return Promise.resolve({ items: [] })
  })
}

function seedPermissions(groupRead: boolean) {
  useAuthStore.setState({
    user: { id: 1, permissions: { ai_skill: { read: true }, ...(groupRead ? { agent_group: { read: true } } : {}) } } as never,
  })
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <OAuthClientsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset()
  apiDelete.mockReset()
  vi.mocked(confirm).mockClear()
  seedPermissions(true)
})

describe('OAuthClientsPage', () => {
  it('flags the app whose redirect host the server does not trust, even when its self-declared name looks legit', async () => {
    mockServer([
      client(1, { client_name: 'ChatGPT', redirect_hosts: ['evil.example'], trusted: false, live_grants: 2 }),
      client(2, { client_name: 'Claude', redirect_hosts: ['claude.ai'], trusted: true, live_grants: 1 }),
    ])
    renderPage()
    expect(await screen.findByText('evil.example')).toBeInTheDocument()
    expect(screen.getAllByText('Host lạ')).toHaveLength(1)
    //  Dòng tóm tắt ghép từ nhiều nút chữ (số · chữ · nhánh host lạ) — so bằng regex trên chữ của chính phần tử.
    expect(screen.getByText(/2 ứng dụng · 3 kết nối đang sống/)).toBeInTheDocument()
    expect(screen.getByText('1 host lạ')).toBeInTheDocument()
  })

  it('asks before deleting, names the app and the live connections that will be cut, then calls DELETE', async () => {
    mockServer([client(7, { client_name: 'ChatGPT', redirect_hosts: ['chatgpt.com'], live_grants: 3 })])
    apiDelete.mockResolvedValue({ revoked_grants: 3 })
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /Xóa ứng dụng ChatGPT/ }))
    expect(confirm).toHaveBeenCalledWith(
      expect.objectContaining({
        confirmLabel: 'Xóa ứng dụng',
        message: expect.stringContaining('3 kết nối đang sống sẽ bị cắt ngay'),
      }),
    )
    await waitFor(() => expect(apiDelete).toHaveBeenCalledWith('/api/agent-hub/oauth-clients/7'))
  })

  it('does nothing when the admin backs out of the confirm box', async () => {
    mockServer([client(7, { client_name: 'ChatGPT' })])
    vi.mocked(confirm).mockResolvedValueOnce(false)
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /Xóa ứng dụng ChatGPT/ }))
    expect(apiDelete).not.toHaveBeenCalled()
  })

  it('hides the delete button when the server says the viewer may not write', async () => {
    mockServer([client(1, { client_name: 'ChatGPT' })], false)
    renderPage()
    expect(await screen.findByText('ChatGPT')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Xóa ứng dụng/ })).not.toBeInTheDocument()
  })

  it('explains instead of calling the API when the viewer lacks the bot-admin permission', () => {
    seedPermissions(false)
    mockServer([client(1)])
    renderPage()
    expect(screen.getByText('Màn này dành cho người quản lý trợ lý AI')).toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('tells where apps come from when the list is empty', async () => {
    mockServer([])
    renderPage()
    expect(await screen.findByText(/Ứng dụng xuất hiện ở đây khi có người bấm "Cho phép"/)).toBeInTheDocument()
  })
})

describe('OAuthClientsPage filters (bao-CR-696)', () => {
  function renderAt(url: string) {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[url]}>
          <OAuthClientsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )
  }

  const apps = [
    client(1, { client_name: 'ChatGPT', live_grants: 2 }),
    client(2, { client_name: 'Trình kết nối lạ', redirect_hosts: ['evil.example'], trusted: false }),
  ]

  it('filters on screen by status from the URL, keeps the totals of the whole list, and asks the server only once', async () => {
    mockServer(apps)
    renderAt('/ai-skill/oauth-clients?status=untrusted')
    expect(await screen.findByText('Trình kết nối lạ')).toBeInTheDocument()
    expect(screen.queryByText('ChatGPT')).not.toBeInTheDocument()
    //  Dòng tóm tắt vẫn nói cả danh sách — lọc không làm "mất" ứng dụng trong con số.
    expect(screen.getByText(/2 ứng dụng · 2 kết nối đang sống/)).toBeInTheDocument()
    expect(apiGet.mock.calls.filter(([u]) => String(u).endsWith('/oauth-clients'))).toHaveLength(1)
  })

  it('searches by redirect host without accents mattering, and says the table is empty because of the filter', async () => {
    const user = userEvent.setup()
    mockServer(apps)
    renderAt('/ai-skill/oauth-clients')
    await screen.findByText('ChatGPT')
    await user.type(screen.getByRole('textbox', { name: 'Tìm ứng dụng' }), 'ket noi')
    await waitFor(() => expect(screen.queryByText('ChatGPT')).not.toBeInTheDocument())
    expect(screen.getByText('Trình kết nối lạ')).toBeInTheDocument()
    await user.clear(screen.getByRole('textbox', { name: 'Tìm ứng dụng' }))
    await user.type(screen.getByRole('textbox', { name: 'Tìm ứng dụng' }), 'khong co ung dung nay')
    expect(await screen.findByText('Không có ứng dụng nào khớp bộ lọc.')).toBeInTheDocument()
  })
})
