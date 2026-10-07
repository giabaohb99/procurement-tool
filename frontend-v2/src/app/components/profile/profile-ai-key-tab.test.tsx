import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { AiKeyInfo, AiKeyItem } from '@/modules/system/api/agent-hub-api'
import { ProfileAiKeyTab } from './profile-ai-key-tab'

/**
 * Tab «Khóa AI» ở Trang cá nhân (ai-CR-053).
 *
 * Chỗ dễ lủng: khóa thô phải đi qua PUT `/api/agent-hub/ai-key` rồi ô nhập XÓA TRẮNG (không để khóa nằm lại
 * trên màn), màn chỉ hiện 4 ký tự cuối do backend trả, và ô nhập là `password`.
 */

const apiGet = vi.fn()
const apiPut = vi.fn()
const apiPost = vi.fn()
const apiDelete = vi.fn()
const apiPatch = vi.fn()

function keyItem(over: Partial<AiKeyItem> = {}): AiKeyItem {
  return { id: 1, provider: 'gemini', provider_label: 'Gemini', model: '', priority: 1, daily_cap: 0, hint: '…0000',
    verified_at: null, used_today: 0, ...over }
}

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: (...args: unknown[]) => apiPut(...args),
  apiPatch: (...args: unknown[]) => apiPatch(...args),
  apiDelete: (...args: unknown[]) => apiDelete(...args),
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: vi.fn(() => Promise.resolve(true)),
}))

function renderTab() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProfileAiKeyTab />
    </QueryClientProvider>,
  )
}

function mockKey(info: Partial<AiKeyInfo> = {}, mcp: { endpoint?: string; items?: unknown[] } = {}) {
  apiGet.mockImplementation((url: string) =>
    url === '/api/agent-hub/mcp-keys'
      ? Promise.resolve({ endpoint: 'https://erp.test/api/mcp', items: [], ...mcp })
      : url === '/api/agent-hub/google'
        ? Promise.resolve({ configured: true, linked: false, email: '', linked_at: null })
        : Promise.resolve({ provider: 'gemini', has_key: false, hint: '', verified_at: null, ...info }),
  )
}

describe('ProfileAiKeyTab', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPut.mockReset()
    apiDelete.mockReset()
  })

  it('saves the raw key through PUT, then clears the input and shows only the hint', async () => {
    mockKey()
    apiPut.mockResolvedValue({ provider: 'gemini', has_key: true, hint: '…9999', verified_at: '2026-09-25T08:00:00' })
    renderTab()
    expect(await screen.findByText(/Chưa có khóa/)).toBeInTheDocument()
    const input = screen.getByLabelText(/Dán khóa Gemini/)
    expect(input).toHaveAttribute('type', 'password')
    await userEvent.type(input, 'AIzaSy-khoa-thu-9999')
    mockKey({ has_key: true, hint: '…9999', verified_at: '2026-09-25T08:00:00', items: [keyItem({ id: 1, hint: '…9999' })] })
    await userEvent.click(screen.getByRole('button', { name: /Lưu khóa/ }))
    await waitFor(() => expect(apiPut).toHaveBeenCalledWith('/api/agent-hub/ai-key', {
      key: 'AIzaSy-khoa-thu-9999', provider: 'gemini', model: '', priority: 0, daily_cap: 0,
    }))
    await waitFor(() => expect(input).toHaveValue(''))
    expect(await screen.findByText('…9999')).toBeInTheDocument()
    expect(screen.queryByText(/AIzaSy-khoa-thu-9999/)).not.toBeInTheDocument()
  })

  it('sends the chosen provider and model when adding a second key (ai-CR-098)', async () => {
    mockKey({ has_key: true, hint: '…1111', items: [keyItem({ id: 1, hint: '…1111' })] })
    apiPut.mockResolvedValue({ provider: 'gemini', has_key: true, hint: '…1111', verified_at: null })
    renderTab()
    await userEvent.selectOptions(await screen.findByLabelText(/Hãng/), 'openrouter')
    await userEvent.type(screen.getByLabelText(/Dán khóa OpenRouter/), 'sk-or-v1-abcdefghijklmnop')
    await userEvent.click(screen.getByRole('button', { name: /Tùy chọn: chọn model/ }))
    await userEvent.type(screen.getByLabelText(/Model \(để trống/), 'anthropic/claude-sonnet-4.5')
    await userEvent.click(screen.getByRole('button', { name: /Lưu khóa/ }))
    await waitFor(() => expect(apiPut).toHaveBeenCalledWith('/api/agent-hub/ai-key', {
      key: 'sk-or-v1-abcdefghijklmnop', provider: 'openrouter', model: 'anthropic/claude-sonnet-4.5', priority: 0, daily_cap: 0,
    }))
  })

  it('removes one key by id after confirmation', async () => {
    mockKey({ has_key: true, hint: '…1234', items: [keyItem({ id: 5, hint: '…1234' })] })
    apiDelete.mockResolvedValue({ provider: 'gemini', has_key: false, hint: '', verified_at: null })
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: /Gỡ khóa/ }))
    await waitFor(() => expect(apiDelete).toHaveBeenCalledWith('/api/agent-hub/ai-key/5'))
  })

  it('moves the second key above the first by swapping priorities', async () => {
    mockKey({ has_key: true, hint: '…1111', items: [
      keyItem({ id: 1, hint: '…1111', priority: 1 }),
      keyItem({ id: 2, hint: '…2222', priority: 2, provider: 'claude', provider_label: 'Claude' }),
    ] })
    apiPatch.mockResolvedValue({})
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: /Đưa khóa …2222 lên trước/ }))
    await waitFor(() => expect(apiPatch).toHaveBeenCalledWith('/api/agent-hub/ai-key/2', { priority: 1 }))
    expect(apiPatch).toHaveBeenCalledWith('/api/agent-hub/ai-key/1', { priority: 2 })
  })

  it('keeps the save button disabled while the input is blank', async () => {
    mockKey()
    renderTab()
    expect(await screen.findByRole('button', { name: /Lưu khóa/ })).toBeDisabled()
    expect(apiGet).toHaveBeenCalledWith('/api/agent-hub/ai-key')
  })
})

describe('ProfileAiKeyTab — khóa MCP (ai-CR-063)', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPost.mockReset()
    apiDelete.mockReset()
  })

  it('creates an MCP key, shows it once with a ready-to-paste config', async () => {
    mockKey()
    apiPost.mockResolvedValue({ id: 3, name: 'Claude', hint: '…abcd', scope: 0, scope_label: 'chỉ đọc', expires_at: null, last_used_at: null, created_at: null, key: 'dego_mcp_xyz' })
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: /Nâng cao: dùng Claude Desktop/ }))
    await userEvent.type(await screen.findByLabelText(/Tên khóa/), 'Claude')
    await userEvent.click(screen.getByRole('button', { name: /Tạo khóa MCP/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/mcp-keys', { name: 'Claude', scope: 0, days: 90 }))
    expect(await screen.findByText('dego_mcp_xyz')).toBeInTheDocument()
    expect(screen.getByText(/"url": "https:\/\/erp.test\/api\/mcp"/)).toBeInTheDocument()
  })

  it('revokes a key through its id', async () => {
    mockKey({}, { items: [{ id: 7, name: 'Cursor', hint: '…9999', scope: 1, scope_label: 'được ghi', expires_at: null, last_used_at: null, created_at: null }] })
    apiDelete.mockResolvedValue(null)
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: /Nâng cao: dùng Claude Desktop/ }))
    const row = (await screen.findByText('Cursor')).closest('li')!
    await userEvent.click(row.querySelector('button')!)
    await waitFor(() => expect(apiDelete).toHaveBeenCalledWith('/api/agent-hub/mcp-keys/7'))
  })
})

describe('ProfileAiKeyTab — Google cá nhân (ai-CR-064)', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPost.mockReset()
  })

  it('asks the backend for the consent URL and navigates there', async () => {
    mockKey()
    apiPost.mockResolvedValue({ url: 'https://accounts.google.com/o/oauth2/v2/auth?x=1' })
    const assign = vi.fn()
    Object.defineProperty(window, 'location', { value: { ...window.location, assign, origin: 'https://erp.test' }, writable: true })
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: /Nối Google/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/google/authorize', {}))
    await waitFor(() => expect(assign).toHaveBeenCalledWith('https://accounts.google.com/o/oauth2/v2/auth?x=1'))
  })
})

describe('ProfileAiKeyTab — dễ dùng (ai-CR-101)', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPatch.mockReset()
    localStorage.clear()
  })

  it('keeps the MCP card collapsed by default and puts the AI key card first', async () => {
    mockKey()
    renderTab()
    const toggle = await screen.findByRole('button', { name: /Nâng cao: dùng Claude Desktop/ })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('button', { name: /Tạo khóa MCP/ })).not.toBeInTheDocument()
    const headings = screen.getAllByText(/Khóa AI của bạn|Google của bạn/)
    expect(headings[0]).toHaveTextContent(/Khóa AI của bạn/)
  })

  it('reads each key as one sentence and edits model and cap only after pressing Sửa', async () => {
    mockKey({ has_key: true, hint: '…1111', items: [keyItem({ id: 3, hint: '…1111', model: 'gemini-flash-latest', daily_cap: 50, used_today: 7 })] })
    apiPatch.mockResolvedValue({})
    renderTab()
    expect(await screen.findByText(/Model: gemini-flash-latest · Trần: 50 lượt\/ngày · Hôm nay 7 lượt/)).toBeInTheDocument()
    expect(screen.queryByLabelText('Trần lượt/ngày')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /Sửa khóa …1111/ }))
    const capInput = screen.getByLabelText('Trần lượt/ngày')
    await userEvent.clear(capInput)
    await userEvent.type(capInput, '0')
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(apiPatch).toHaveBeenCalledWith('/api/agent-hub/ai-key/3', { model: 'gemini-flash-latest', daily_cap: 0 }))
  })

  it('links the "get key" button to the chosen provider site', async () => {
    mockKey()
    renderTab()
    await userEvent.selectOptions(await screen.findByLabelText(/Hãng/), 'claude')
    expect(screen.getByRole('link', { name: /Mở trang Claude/ })).toHaveAttribute('href', 'https://console.anthropic.com/')
  })
})

