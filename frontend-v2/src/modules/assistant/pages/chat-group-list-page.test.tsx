import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ChatGroupItem, ChatGroupMeta } from '../api/chat-group-api'
import { ChatGroupListPage } from './chat-group-list-page'

/**
 * Màn «Nhóm chat» (ai-CR-123). Chỗ dễ lủng: người thường KHÔNG được thấy lối «Tất cả nhóm» (đại ca chốt 08/10: chỉ
 * quản lý bot AI thấy hết), và danh sách phải xin đúng `scope` — gửi nhầm `all` cho người thường thì backend vẫn chặn,
 * nhưng gửi `mine` cho người quản lý là họ tưởng bot chưa ở nhóm nào.
 */

const apiGet = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
  extractErrorMessage: (e: unknown) => String(e),
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() } }))

const baseMeta: ChatGroupMeta = {
  categories: [
    { value: 0, label: 'Chưa phân loại' },
    { value: 2, label: 'Dự án' },
  ],
  channels: [{ value: 'telegram', label: 'Telegram' }],
  can_view_all: false,
  can_manage: false,
  retention_days: 90,
  zalo_enabled: false,
}

const group: ChatGroupItem = {
  id: 7,
  title: 'Kế toán DEGO',
  channel: 'zalo_account',
  channel_label: 'Zalo (tài khoản công ty)',
  category: 0,
  category_label: 'Chưa phân loại',
  active: true,
  paused: false,
  is_member: true,
  is_owner: true,
  owner_user_id: 1,
  owner_label: 'Chị Mi',
  members_count: 5,
  message_count: 12,
  file_count: 1,
  last_message_at: '2026-10-08T09:00:00',
  joined_at: null,
  can_edit: true,
}

function mockApi(meta: Partial<ChatGroupMeta>) {
  apiGet.mockImplementation((raw: unknown) => {
    const url = String(raw ?? '')
    if (url.endsWith('/groups/meta')) return Promise.resolve({ ...baseMeta, ...meta })
    if (url.endsWith('/zalo/status')) return Promise.resolve({ enabled: true, state: 'connected' })
    return Promise.resolve({ items: [group], total: 1, can_view_all: false, can_manage: false })
  })
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ChatGroupListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function lastListScope(): unknown {
  const calls = apiGet.mock.calls.filter(([url]) => String(url).endsWith('/api/agent-hub/groups'))
  const last = calls[calls.length - 1]
  return (last?.[1] as { params?: { scope?: string } } | undefined)?.params?.scope
}

describe('ChatGroupListPage', () => {
  beforeEach(() => apiGet.mockReset())

  it('hides the all-groups tab from a regular user and only asks for their own groups', async () => {
    mockApi({ can_view_all: false })
    renderPage()
    expect(await screen.findByText('Kế toán DEGO')).toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: 'Tất cả nhóm' })).not.toBeInTheDocument()
    expect(lastListScope()).toBe('mine')
  })

  it('lets an AI manager switch to every group the bot is in', async () => {
    mockApi({ can_view_all: true })
    renderPage()
    const tab = await screen.findByRole('tab', { name: 'Tất cả nhóm' })
    await userEvent.click(tab)
    await waitFor(() => expect(lastListScope()).toBe('all'))
  })
})
