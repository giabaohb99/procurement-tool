import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { TelegramLinksResult } from '@/modules/system/api/agent-hub-api'
import { ProfileTelegramTab } from './profile-telegram-tab'

/**
 * Tab «Telegram» ở Trang cá nhân (ai-CR-038).
 *
 * Chỗ dễ lủng: cửa gọi phải là `/api/agent-hub/links*` (tự phục vụ, chỉ đòi đăng nhập), và mã
 * một lần phải hiện kèm lệnh chép sẵn — người dùng gõ nhầm lệnh là bot im lặng (chat lạ bị lờ).
 * Không có chỗ nào trong tab hỏi mật khẩu.
 */

const apiGet = vi.fn()
const apiPost = vi.fn()
const apiDelete = vi.fn()
const apiPatch = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: vi.fn(),
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
      <ProfileTelegramTab />
    </QueryClientProvider>,
  )
}

function mockLinks(result: Partial<TelegramLinksResult> = {}) {
  apiGet.mockResolvedValue({ enabled: true, bot_username: '', items: [], ...result })
}

describe('ProfileTelegramTab', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPost.mockReset()
    apiDelete.mockReset()
  })

  it('issues a one-time code from the self-service endpoint and shows it', async () => {
    mockLinks()
    apiPost.mockResolvedValue({ code: '042917', expires_at: '2026-09-24T08:10:00', deep_link: '' })
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: /Lấy mã liên kết/ }))
    expect(await screen.findByText('042917')).toBeInTheDocument()
    expect(apiGet).toHaveBeenCalledWith('/api/agent-hub/links')
    expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/links/code', {})
    //  Chưa khai tên bot thì không có link mở thẳng bot.
    expect(screen.queryByText(/Mở bot và đăng nhập luôn/)).not.toBeInTheDocument()
  })

  it('offers the deep link only when the backend built one', async () => {
    mockLinks({ bot_username: 'daudau_bot' })
    apiPost.mockResolvedValue({ code: '111111', expires_at: null, deep_link: 'https://t.me/daudau_bot?start=111111' })
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: /Lấy mã liên kết/ }))
    const link = await screen.findByRole('link', { name: /Mở bot và đăng nhập luôn/ })
    expect(link).toHaveAttribute('href', 'https://t.me/daudau_bot?start=111111')
  })

  it('removes a linked chat through its own id', async () => {
    mockLinks({
      items: [{ id: 9, chat: '…4321', tg_name: 'Lan', linked_at: '2026-09-24T08:00:00', expires_at: '2026-10-24T08:00:00', notify_mode: 1 }],
    })
    apiDelete.mockResolvedValue(null)
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: /Gỡ/ }))
    await waitFor(() => expect(apiDelete).toHaveBeenCalledWith('/api/agent-hub/links/9'))
  })

  it('says linking is off instead of showing a dead button', async () => {
    mockLinks({ enabled: false })
    renderTab()
    expect(await screen.findByText(/đang tắt/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Lấy mã liên kết/ })).not.toBeInTheDocument()
  })
})

describe('ProfileTelegramTab — chuông (ai-CR-059)', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPatch.mockReset()
  })

  it('changes the bell mode of a link through PATCH', async () => {
    mockLinks({
      items: [{ id: 9, chat: '…4321', tg_name: 'Lan', linked_at: '2026-09-24T08:00:00', expires_at: '2026-10-24T08:00:00', notify_mode: 1 }],
    })
    apiPatch.mockResolvedValue({ id: 9, notify_mode: 2 })
    renderTab()
    const select = await screen.findByLabelText(/Chuông ERP cho Lan/)
    expect(select).toHaveValue('1')
    await userEvent.selectOptions(select, '2')
    await waitFor(() => expect(apiPatch).toHaveBeenCalledWith('/api/agent-hub/links/9', { notify_mode: 2 }))
  })
})
