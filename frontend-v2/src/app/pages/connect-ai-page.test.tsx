import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ConnectAiPage } from './connect-ai-page'

/**
 * Trang công khai /connect-ai (bao-CR-638). Chỗ không được lủng: KHÔNG BAO GIỜ có khóa — chỉ gọi đường công khai
 * `mcp-setup/public`, không gọi đường khóa của người dùng (kể cả khi trình duyệt còn phiên đăng nhập), đoạn cấu hình giữ
 * nguyên chỗ giữ khóa, và trong trang không có chuỗi `dego_mcp_` nào.
 */

const apiGet = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

const PLACEHOLDER = '<KHÓA_CỦA_BẠN>'

function mockPublic() {
  apiGet.mockImplementation((url: string, config?: { params?: { client?: string } }) => {
    if (url === '/api/agent-hub/mcp-setup/public' && config?.params?.client === 'chatgpt') {
      return Promise.resolve({ client: 'chatgpt', label: 'ChatGPT', supported: true, auth: 'oauth', format: 'url',
        snippet: 'https://erp.test/api/mcp', steps: ['Mở Connectors'], endpoint: 'https://erp.test/api/mcp', placeholder: PLACEHOLDER })
    }
    if (url === '/api/agent-hub/mcp-setup/public' && config?.params?.client) {
      return Promise.resolve({ client: 'cursor', label: 'Cursor', supported: true, auth: 'key', format: 'json',
        snippet: `{"headers":{"Authorization":"Bearer ${PLACEHOLDER}"}}`, steps: ['Mở Cursor'],
        endpoint: 'https://erp.test/api/mcp', placeholder: PLACEHOLDER })
    }
    if (url === '/api/agent-hub/mcp-setup/public') {
      return Promise.resolve({ endpoint: 'https://erp.test/api/mcp', placeholder: PLACEHOLDER, clients: [
        { client: 'cursor', label: 'Cursor', supported: true, auth: 'key' },
        { client: 'chatgpt', label: 'ChatGPT', supported: true, auth: 'oauth' },
      ] })
    }
    //  Phiên đăng nhập còn sống mà trang lỡ gọi đường khóa thì khóa thật sẽ lọt ra — giả lập đúng tình huống đó.
    return Promise.resolve({ items: [{ id: 1, key: 'dego_mcp_leak' }], key: 'dego_mcp_leak' })
  })
}

function renderPage(path = '/connect-ai') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <ConnectAiPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset()
})

describe('ConnectAiPage', () => {
  it('uses only the public setup endpoint and keeps the key placeholder in the config', async () => {
    mockPublic()
    const { container } = renderPage()
    expect(await screen.findByText(/Bearer <KHÓA_CỦA_BẠN>/)).toBeInTheDocument()
    expect(apiGet.mock.calls.every(([url]) => url === '/api/agent-hub/mcp-setup/public')).toBe(true)
    expect(container.textContent).not.toMatch(/dego_mcp_/)
  })

  it('opens the app named in ?client= and shows only the address for an OAuth app', async () => {
    mockPublic()
    const { container } = renderPage('/connect-ai?client=chatgpt')
    expect(await screen.findByText('Địa chỉ kết nối')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ChatGPT/ })).toHaveAttribute('aria-pressed', 'true')
    expect(container.textContent).not.toMatch(/dego_mcp_|KHÓA_CỦA_BẠN/)
  })

  it('copies the config with the placeholder, never asking for a key', async () => {
    const writeText = vi.fn(() => Promise.resolve())
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
    mockPublic()
    renderPage('/connect-ai?client=cursor')
    await userEvent.click(await screen.findByRole('button', { name: 'Sao chép đoạn cấu hình' }))
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(`{"headers":{"Authorization":"Bearer ${PLACEHOLDER}"}}`))
    expect(apiGet.mock.calls.every(([url]) => url === '/api/agent-hub/mcp-setup/public')).toBe(true)
  })

  it('ignores an unknown ?client= and falls back to the first supported app', async () => {
    mockPublic()
    renderPage('/connect-ai?client=<script>')
    expect(await screen.findByRole('button', { name: /Cursor/ })).toHaveAttribute('aria-pressed', 'true')
  })
})
