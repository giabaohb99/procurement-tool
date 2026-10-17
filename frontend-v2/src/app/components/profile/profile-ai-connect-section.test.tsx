import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { confirm } from '@/shared/ui/confirm-dialog'
import { ProfileAiConnectSection } from './profile-ai-connect-section'

/**
 * Mục «Kết nối AI riêng» (P0 doc 21 — tách từ khối MCP «Nâng cao» của tab Khóa AI, ai-CR-063).
 *
 * Chỗ dễ lủng: khóa thô chỉ có trong phản hồi lúc TẠO và phải hiện đúng một lần kèm đoạn cấu hình dán được; gỡ khóa
 * phải đi theo id và chỉ sau khi người dùng xác nhận; tiêu đề viết cho nhân viên văn phòng, không chữ MCP.
 */

const apiGet = vi.fn()
const apiPost = vi.fn()
const apiDelete = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: (...args: unknown[]) => apiDelete(...args),
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: vi.fn(() => Promise.resolve(true)),
}))

function mockKeys(payload: { endpoint?: string; items?: unknown[] } = {}) {
  apiGet.mockImplementation((url: string) =>
    url === '/api/agent-hub/mcp-keys'
      ? Promise.resolve({ endpoint: 'https://erp.test/api/mcp', items: [], ...payload })
      : Promise.resolve(null),
  )
}

function keyRow(over: Record<string, unknown> = {}) {
  return { id: 7, name: 'Cursor', hint: '…9999', scope: 1, scope_label: 'được ghi', expires_at: null, last_used_at: null, created_at: null, ...over }
}

function renderSection() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProfileAiConnectSection />
    </QueryClientProvider>,
  )
}

describe('ProfileAiConnectSection', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPost.mockReset()
    apiDelete.mockReset()
    vi.mocked(confirm).mockClear()
    vi.mocked(confirm).mockResolvedValue(true)
  })

  it('is open straight away, not hidden behind an Advanced toggle, and titled without the word MCP', async () => {
    mockKeys()
    renderSection()
    expect(await screen.findByRole('button', { name: /Tạo khóa/ })).toBeVisible()
    expect(await screen.findByText(/Chưa có khóa nào/)).toBeInTheDocument()
    for (const heading of screen.getAllByRole('heading')) expect(heading.textContent).not.toMatch(/MCP/)
  })

  it('creates a read-only 90-day key by default and shows it once with a ready-to-paste config', async () => {
    mockKeys()
    apiPost.mockResolvedValue({ id: 3, name: 'Claude', hint: '…abcd', scope: 0, scope_label: 'chỉ đọc', expires_at: null, last_used_at: null, created_at: null, key: 'dego_mcp_xyz' })
    renderSection()
    await userEvent.type(await screen.findByLabelText('Tên khóa'), 'Claude')
    await userEvent.click(screen.getByRole('button', { name: /Tạo khóa/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/mcp-keys', { name: 'Claude', scope: 0, days: 90 }))
    expect(await screen.findByText('dego_mcp_xyz')).toBeInTheDocument()
    expect(screen.getByText(/"url": "https:\/\/erp.test\/api\/mcp"/)).toBeInTheDocument()
    expect(screen.getByText(/"Authorization": "Bearer dego_mcp_xyz"/)).toBeInTheDocument()
  })

  it('sends the write scope only when the user picks it', async () => {
    mockKeys()
    apiPost.mockResolvedValue({ id: 4, name: '', hint: '…ffff', scope: 1, scope_label: 'được ghi', expires_at: null, last_used_at: null, created_at: null, key: 'dego_mcp_w' })
    renderSection()
    await userEvent.selectOptions(await screen.findByLabelText('Mức'), '1')
    await userEvent.click(screen.getByRole('button', { name: /Tạo khóa/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/mcp-keys', { name: '', scope: 1, days: 90 }))
  })

  it('revokes a key through its id after confirmation', async () => {
    mockKeys({ items: [keyRow()] })
    apiDelete.mockResolvedValue(null)
    renderSection()
    await userEvent.click(await screen.findByRole('button', { name: 'Gỡ khóa Cursor' }))
    await waitFor(() => expect(apiDelete).toHaveBeenCalledWith('/api/agent-hub/mcp-keys/7'))
  })

  it('does not revoke when the user cancels the confirmation', async () => {
    mockKeys({ items: [keyRow()] })
    vi.mocked(confirm).mockResolvedValue(false)
    renderSection()
    await userEvent.click(await screen.findByRole('button', { name: 'Gỡ khóa Cursor' }))
    await waitFor(() => expect(confirm).toHaveBeenCalled())
    expect(apiDelete).not.toHaveBeenCalled()
  })

  it('falls back to the current site address when the server sends no endpoint', async () => {
    mockKeys({ endpoint: '' })
    renderSection()
    expect(await screen.findByText(`${window.location.origin}/api/mcp`)).toBeInTheDocument()
  })
})
