import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
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
  it('shows the ERP-login way (OAuth) first and keeps the key way folded', async () => {
    //  kh-AI-ket-noi-giao-dien: mở màn là thấy Cách 1 — đăng nhập ERP, không cần khóa. Cách 2 (khóa riêng) là phần
    //  Nâng cao, thu gọn và CHƯA gọi chi tiết ứng dụng dùng khóa.
    mockPublic()
    const { container } = renderPage()
    expect(await screen.findByText('Địa chỉ kết nối')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /ChatGPT/ })).toHaveAttribute('aria-pressed', 'true')
    const advanced = screen.getByRole('button', { name: /Cách 2 \(nâng cao\)/ })
    expect(advanced).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('button', { name: /Cursor/ })).not.toBeInTheDocument()
    expect(container.textContent).not.toMatch(/dego_mcp_|KHÓA_CỦA_BẠN/)
  })

  it('opens the key way on demand, with the placeholder kept and only the public endpoint called', async () => {
    mockPublic()
    const { container } = renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /Cách 2 \(nâng cao\)/ }))
    expect(await screen.findByText(/Bearer <KHÓA_CỦA_BẠN>/)).toBeInTheDocument()
    expect(apiGet.mock.calls.every(([url]) => url === '/api/agent-hub/mcp-setup/public')).toBe(true)
    expect(container.textContent).not.toMatch(/dego_mcp_/)
  })

  it('opens the key way straight away when ?client= names a key app', async () => {
    mockPublic()
    renderPage('/connect-ai?client=cursor')
    expect(await screen.findByRole('button', { name: /Cursor/ })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: /Cách 2 \(nâng cao\)/ })).toHaveAttribute('aria-expanded', 'true')
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

  it('ignores an unknown ?client= and falls back to the first ERP-login app', async () => {
    mockPublic()
    renderPage('/connect-ai?client=<script>')
    expect(await screen.findByRole('button', { name: /ChatGPT/ })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: /Cách 2 \(nâng cao\)/ })).toHaveAttribute('aria-expanded', 'false')
  })

  it('keeps one plain list against an older server that does not say which apps use OAuth', async () => {
    apiGet.mockImplementation((url: string, config?: { params?: { client?: string } }) => {
      if (url === '/api/agent-hub/mcp-setup/public' && config?.params?.client) {
        return Promise.resolve({ client: 'cursor', label: 'Cursor', supported: true, format: 'json', snippet: '{}',
          steps: [], endpoint: 'https://erp.test/api/mcp', placeholder: PLACEHOLDER })
      }
      return Promise.resolve({ endpoint: 'https://erp.test/api/mcp', placeholder: PLACEHOLDER,
        clients: [{ client: 'cursor', label: 'Cursor', supported: true }] })
    })
    renderPage()
    expect(await screen.findByRole('button', { name: /Cursor/ })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.queryByRole('button', { name: /Cách 2 \(nâng cao\)/ })).not.toBeInTheDocument()
  })

  it('keeps the intro short and links to the full help article', async () => {
    mockPublic()
    renderPage()
    const link = await screen.findByRole('link', { name: /AI riêng của bạn làm được gì trong ERP/ })
    expect(link.getAttribute('href')).toMatch(/\/ai-rieng-cua-ban-lam-duoc-gi-trong-erp-cong-cu-va-skill$/)
  })

  it('names both ways exactly like their help articles and links each to its own article', async () => {
    //  Tên trên màn phải khớp tên bài ở Trung tâm trợ giúp (seed_help_ket_noi_ai_cach_1.py), lệch là người dùng tìm không ra.
    mockPublic()
    renderPage()
    const oauth = await screen.findByRole('region', { name: 'Cách 1 (khuyên dùng): nối bằng đăng nhập ERP' })
    const key = screen.getByRole('region', { name: 'Cách 2 (nâng cao): sửa tệp cấu hình bằng khóa riêng' })
    expect(within(oauth).getByRole('link', { name: /Xem bài hướng dẫn/ }).getAttribute('href')).toMatch(
      /\/cach-1-khuyen-dung-noi-bang-dang-nhap-erp$/,
    )
    expect(within(key).getByRole('link', { name: /Xem bài hướng dẫn/ }).getAttribute('href')).toMatch(
      /\/cach-2-nang-cao-sua-tep-cau-hinh-bang-khoa-rieng$/,
    )
  })
})
