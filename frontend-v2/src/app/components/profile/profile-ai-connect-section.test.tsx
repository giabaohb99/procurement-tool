import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { confirm } from '@/shared/ui/confirm-dialog'
import { ProfileAiConnectSection } from './profile-ai-connect-section'

/**
 * «Kết nối AI riêng» = màn «AI của tôi» (G8, K6 bao-CR-624; tách từ khối MCP «Nâng cao» ở P0).
 *
 * Chỗ dễ lủng:
 * - Khóa thô chỉ có trong phản hồi lúc TẠO / NHẬN, hiện đúng một lần — và đoạn cấu hình ở bước 1 phải tự điền khóa đó
 *   vào chỗ giữ, không thì người dùng dán nguyên `<KHÓA_CỦA_BẠN>` vào ứng dụng rồi kêu không nối được.
 * - Ứng dụng chưa hỗ trợ (claude.ai, ChatGPT) không được hiện đoạn cấu hình rỗng như thể dùng được.
 * - Gỡ khóa đi theo id và chỉ sau khi xác nhận.
 * - Tiêu đề viết cho nhân viên văn phòng, không chữ MCP.
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
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: vi.fn(() => Promise.resolve(true)) }))

const PLACEHOLDER = '<KHÓA_CỦA_BẠN>'

function keyRow(over: Record<string, unknown> = {}) {
  return {
    id: 7, name: 'Cursor', hint: '…9999', scope: 0, scope_label: 'chỉ đọc', expires_at: null, last_used_at: null,
    created_at: null, state: 2, state_label: 'Đang dùng', issued_by: 0, claimed_at: null, batch_id: '', user_id: 3, ...over,
  }
}

interface ServerState {
  myKeys?: unknown[]
  pending?: unknown[]
  lastCall?: unknown
  skills?: unknown[]
}

function mockServer(state: ServerState = {}) {
  apiGet.mockImplementation((url: string, config?: { params?: { client?: string } }) => {
    if (url === '/api/agent-hub/mcp-setup' && config?.params?.client === 'chatgpt') {
      return Promise.resolve({ client: 'chatgpt', label: 'ChatGPT', supported: false, format: '', snippet: '', steps: [],
        note: 'ChatGPT chưa nối được kết nối riêng của công ty.', endpoint: 'https://erp.test/api/mcp', placeholder: PLACEHOLDER })
    }
    if (url === '/api/agent-hub/mcp-setup' && config?.params?.client) {
      return Promise.resolve({ client: 'claude_desktop', label: 'Claude Desktop', supported: true, format: 'json',
        snippet: `{"env":{"DEGO_MCP_KEY":"${PLACEHOLDER}"}}`, steps: ['Mở Settings', 'Dán đoạn dưới'],
        files: { windows: '%APPDATA%\\Claude\\claude_desktop_config.json' }, requires: ['Node.js'],
        endpoint: 'https://erp.test/api/mcp', placeholder: PLACEHOLDER })
    }
    if (url === '/api/agent-hub/mcp-setup') {
      return Promise.resolve({ endpoint: 'https://erp.test/api/mcp', placeholder: PLACEHOLDER, clients: [
        { client: 'claude_desktop', label: 'Claude Desktop', supported: true },
        { client: 'chatgpt', label: 'ChatGPT', supported: false },
      ] })
    }
    if (url === '/api/agent-hub/mcp-keys') return Promise.resolve({ endpoint: 'https://erp.test/api/mcp', items: state.myKeys ?? [] })
    if (url === '/api/agent-hub/mcp-keys/pending') return Promise.resolve({ items: state.pending ?? [] })
    if (url.endsWith('/last-call')) return Promise.resolve(state.lastCall ?? { key_id: 7, connected: false, last_call: null, last_ok_call: null })
    if (url === '/api/ai-skills/me') return Promise.resolve({ items: state.skills ?? [] })
    if (url === '/api/agent-hub/mcp-calls') return Promise.resolve({ total: 0, page: 1, size: 20, has_more: false, items: [], statuses: [] })
    return Promise.resolve(null)
  })
}

function renderSection() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProfileAiConnectSection />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset()
  apiPost.mockReset()
  apiDelete.mockReset()
  vi.mocked(confirm).mockClear()
  vi.mocked(confirm).mockResolvedValue(true)
})

describe('ProfileAiConnectSection (AI của tôi)', () => {
  it('opens straight on step 1 with the first supported app and its config, titles free of the word MCP', async () => {
    mockServer()
    renderSection()
    expect(await screen.findByText('Bước 1 · Chọn ứng dụng AI bạn đang dùng')).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /Claude Desktop/ })).toHaveAttribute('aria-pressed', 'true')
    expect(await screen.findByText(/"DEGO_MCP_KEY":"<KHÓA_CỦA_BẠN>"/)).toBeInTheDocument()
    expect(screen.getByText(/Cần cài trước: Node.js/)).toBeInTheDocument()
    for (const heading of screen.getAllByRole('heading')) expect(heading.textContent).not.toMatch(/MCP/)
  })

  it('shows the reason instead of an empty config for an app that cannot connect', async () => {
    mockServer()
    renderSection()
    await userEvent.click(await screen.findByRole('button', { name: /ChatGPT/ }))
    expect(await screen.findByText(/ChatGPT chưa nối được/)).toBeInTheDocument()
    expect(screen.queryByText('Đoạn cấu hình dán vào tệp')).not.toBeInTheDocument()
  })

  it('creates a read-only 90-day key, shows it once and fills it into the step 1 config', async () => {
    mockServer()
    apiPost.mockResolvedValue({ ...keyRow({ id: 3, name: 'Claude', hint: '…abcd' }), key: 'dego_mcp_xyz' })
    renderSection()
    await userEvent.type(await screen.findByLabelText('Tên khóa'), 'Claude')
    await userEvent.click(screen.getByRole('button', { name: /Tạo khóa/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/mcp-keys', { name: 'Claude', scope: 0, days: 90 }))
    expect(await screen.findByText('dego_mcp_xyz')).toBeInTheDocument()
    expect(await screen.findByText(/"DEGO_MCP_KEY":"dego_mcp_xyz"/)).toBeInTheDocument()
    expect(screen.queryByText(/<KHÓA_CỦA_BẠN>/)).not.toBeInTheDocument()
  })

  it('claims a key issued by an admin and reveals it once', async () => {
    mockServer({ pending: [keyRow({ id: 11, name: 'Khóa phòng Thu mua', state: 1, state_label: 'Chờ nhận' })] })
    apiPost.mockResolvedValue({ ...keyRow({ id: 11, name: 'Khóa phòng Thu mua' }), key: 'dego_mcp_claimed' })
    renderSection()
    await userEvent.click(await screen.findByRole('button', { name: 'Nhận khóa' }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/mcp-keys/11/claim'))
    expect(await screen.findByText('dego_mcp_claimed')).toBeInTheDocument()
  })

  it('revokes a key through its id after confirmation, and not when cancelled', async () => {
    mockServer({ myKeys: [keyRow()] })
    apiDelete.mockResolvedValue(null)
    renderSection()
    vi.mocked(confirm).mockResolvedValueOnce(false)
    await userEvent.click(await screen.findByRole('button', { name: 'Gỡ khóa Cursor' }))
    await waitFor(() => expect(confirm).toHaveBeenCalledTimes(1))
    expect(apiDelete).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Gỡ khóa Cursor' }))
    await waitFor(() => expect(apiDelete).toHaveBeenCalledWith('/api/agent-hub/mcp-keys/7'))
  })

  it('reports a working connection from the last successful call of the key', async () => {
    mockServer({
      myKeys: [keyRow()],
      lastCall: { key_id: 7, connected: true, last_call: null,
        last_ok_call: { created_at: '2026-10-17T09:00:00', client_name: 'Claude Desktop', method: 'tools/call', tool: 'my_tasks', status: 1, status_label: 'Thành công', deny_reason: '' } },
    })
    renderSection()
    expect(await screen.findByText(/Đã nối\. Lượt thành công gần nhất .* từ Claude Desktop \(công cụ my_tasks\)/)).toBeInTheDocument()
    await waitFor(() => expect(apiGet).toHaveBeenCalledWith('/api/agent-hub/mcp-keys/7/last-call'))
  })

  it('explains what to do next when the key has never connected, with the refusal reason of the last try', async () => {
    mockServer({
      myKeys: [keyRow()],
      lastCall: { key_id: 7, connected: false, last_ok_call: null,
        last_call: { created_at: '2026-10-17T09:00:00', client_name: 'Cursor', method: 'tools/call', tool: 'payable_lookup', status: 2, status_label: 'Bị từ chối', deny_reason: 'Không có quyền' } },
    })
    renderSection()
    expect(await screen.findByText(/Chưa thấy lượt thành công nào/)).toBeInTheDocument()
    expect(screen.getByText(/Không có quyền/)).toBeInTheDocument()
  })

  it('lists the skills the user’s AI can read, or says none is assigned', async () => {
    mockServer({ skills: [{ skill_id: 1, slug: 'quy-trinh-mua', title: 'Quy trình mua', summary: 'Dùng khi hỏi mua hàng.',
      version_no: 2, version_id: 9, updated_at: null, skill_set_id: 4, skill_set: 'Thu mua', security_level: 1, security_level_label: 'Mở' }] })
    renderSection()
    const card = (await screen.findByText('AI của bạn đang đọc được (1)')).closest('[data-slot="card"]') as HTMLElement
    expect(within(card).getByText('Quy trình mua')).toBeInTheDocument()
    expect(within(card).getByText(/Thu mua · v2/)).toBeInTheDocument()
  })
})
