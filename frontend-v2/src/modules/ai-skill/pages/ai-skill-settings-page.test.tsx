import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { McpSettings } from '../types/ai-skill'
import { AiSkillSettingsPage } from './ai-skill-settings-page'

/**
 * Cấu hình cổng MCP (G7). Thiếu `agent_group.read` thì không gọi API; thiếu quyền ghi (`can_write` false) thì không
 * có nút lưu; lưu chỉ gửi phần đã đổi; bấm đúp chỉ ra một request; ô số sai thì chặn lưu.
 */

const apiGet = vi.fn()
const apiPut = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPut: (...args: unknown[]) => apiPut(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))

function settings(over: Partial<McpSettings> = {}): McpSettings {
  return {
    groups: [
      { key: 'mine', label: 'Tra cứu của chính mình', enabled: true, default: true, tools: ['my_tickets'] },
      { key: 'finance', label: 'Công nợ và thanh toán', enabled: false, default: false, tools: ['payable_lookup'] },
    ],
    limits: [{ key: 'rate_per_key', label: 'Lượt / phút / khóa', value: 60, default: 60, min: 10, max: 2000 }],
    extra_instructions: '',
    extra_max_len: 1000,
    can_write: true,
    ...over,
  }
}

function grant(groupRead: boolean) {
  useAuthStore.setState({
    user: { id: 1, permissions: { ai_skill: { read: true }, ...(groupRead ? { agent_group: { read: true } } : {}) } } as never,
  })
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AiSkillSettingsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset()
  apiPut.mockReset()
})

describe('AiSkillSettingsPage', () => {
  it('explains the missing right and never calls the settings without agent_group.read', () => {
    grant(false)
    renderPage()
    expect(screen.getByText('Cấu hình dành cho người quản lý trợ lý AI')).toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('shows a read-only view without a save button when the server says can_write is false', async () => {
    grant(true)
    apiGet.mockResolvedValue(settings({ can_write: false }))
    renderPage()
    expect(await screen.findByText(/chế độ chỉ đọc/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Lưu cấu hình/ })).not.toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'Công nợ và thanh toán' })).toBeDisabled()
    //  Ô số chỉ xem dùng readOnly, không disabled — vẫn bôi đen, copy được.
    expect(screen.getByLabelText('Lượt / phút / khóa')).toHaveAttribute('readonly')
  })

  it('sends only the toggled group once, even on a double click', async () => {
    grant(true)
    apiGet.mockResolvedValue(settings())
    let resolve: (v: McpSettings) => void = () => {}
    apiPut.mockReturnValue(new Promise<McpSettings>((r) => (resolve = r)))
    renderPage()
    fireEvent.click(await screen.findByRole('switch', { name: 'Công nợ và thanh toán' }))
    const saveButton = screen.getByRole('button', { name: /Lưu cấu hình/ })
    fireEvent.click(saveButton)
    fireEvent.click(saveButton)
    await waitFor(() => expect(apiPut).toHaveBeenCalledTimes(1))
    expect(apiPut).toHaveBeenCalledWith('/api/agent-hub/mcp-settings', { groups: { finance: true } })
    resolve(settings({ can_write: undefined, groups: settings().groups.map((g) => ({ ...g, enabled: true })) }))
    //  PUT không trả can_write — màn vẫn phải giữ chế độ sửa.
    expect(await screen.findByRole('button', { name: /Lưu cấu hình/ })).toBeInTheDocument()
  })

  it('blocks saving when a limit is out of range and says the range', async () => {
    grant(true)
    apiGet.mockResolvedValue(settings())
    renderPage()
    fireEvent.change(await screen.findByLabelText('Lượt / phút / khóa'), { target: { value: '5' } })
    expect(screen.getByText('Chỉ nhận từ 10 tới 2000.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Lưu cấu hình/ })).toBeDisabled()
    fireEvent.submit(screen.getByRole('button', { name: /Lưu cấu hình/ }).closest('form') as HTMLFormElement)
    expect(apiPut).not.toHaveBeenCalled()
  })
})
