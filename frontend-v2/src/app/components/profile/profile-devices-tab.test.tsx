import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { LoginSessionItem, MySessionsResult } from '@/modules/system/api/login-session-api'
import { ProfileDevicesTab } from './profile-devices-tab'

/**
 * Tab «Thiết bị của tôi» ở Trang cá nhân (bao-CR-395).
 *
 * Chỗ dễ lủng: phiên ĐANG BẤM không được có nút đăng xuất — người dùng tự đá
 * chính mình rồi trang đứng im tới 60 giây (cache hồ sơ quyền) trước khi văng
 * ra màn đăng nhập, không hiểu chuyện gì xảy ra. Muốn thoát máy này thì bấm
 * Đăng xuất như thường. Và cửa gọi phải là `/api/auth/sessions*` (tự phục vụ,
 * chỉ đòi đăng nhập), KHÔNG phải `/api/login-sessions*` (đòi khóa quản trị).
 */

const apiGet = vi.fn()
const apiPost = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: vi.fn(() => Promise.resolve(true)),
}))

function makeSession(overrides: Partial<LoginSessionItem> = {}): LoginSessionItem {
  return {
    id: 1,
    user_id: 7,
    user_name: 'Tôi',
    ip: '10.0.0.1',
    last_seen_ip: '10.0.0.1',
    device_type: 1,
    device_type_label: 'Máy tính',
    os: 'Windows',
    browser: 'Chrome',
    device_label: 'Chrome trên Windows',
    user_agent: 'Mozilla/5.0',
    login_method: 1,
    login_method_label: 'Mật khẩu',
    created_at: '2026-09-14T08:00:00',
    last_seen_at: '2026-09-14T09:00:00',
    refreshed_at: null,
    refresh_count: 0,
    expires_at: null,
    revoked_at: null,
    revoked_by: 0,
    revoked_by_name: '',
    revoke_reason: null,
    revoke_reason_label: '',
    is_alive: true,
    ending: 'Còn hiệu lực',
    is_current: false,
    ...overrides,
  }
}

function renderTab() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProfileDevicesTab />
    </QueryClientProvider>,
  )
}

function mockSessions(items: LoginSessionItem[], currentId = 1) {
  const result: MySessionsResult = { items, current_session_id: currentId }
  apiGet.mockResolvedValue(result)
}

describe('ProfileDevicesTab', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPost.mockReset()
    apiPost.mockResolvedValue({ revoked: 1 })
  })

  it('reads the self-service endpoint, not the admin one', async () => {
    mockSessions([makeSession({ is_current: true })])
    renderTab()
    await screen.findByText('Thiết bị này')
    expect(apiGet).toHaveBeenCalledWith('/api/auth/sessions', { params: { active_only: true } })
    expect(apiGet).not.toHaveBeenCalledWith('/api/login-sessions', expect.anything())
  })

  it('never offers a logout button on the session currently in use', async () => {
    mockSessions([
      makeSession({ id: 1, is_current: true }),
      makeSession({ id: 2, device_label: 'Safari trên iOS' }),
    ])
    renderTab()
    await screen.findByText('Safari trên iOS')
    // Đúng MỘT nút «Đăng xuất» theo dòng — của máy kia; máy đang bấm không có.
    const rowButtons = screen.getAllByRole('button', { name: /^Đăng xuất$/ })
    expect(rowButtons).toHaveLength(1)
  })

  it('kicks another device through /api/auth/sessions/{id}/revoke', async () => {
    mockSessions([makeSession({ id: 1, is_current: true }), makeSession({ id: 2 })])
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: /^Đăng xuất$/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/auth/sessions/2/revoke', {}))
  })

  it('disables "log out all others" when this is the only live session', async () => {
    mockSessions([makeSession({ is_current: true })])
    renderTab()
    await screen.findByText('Thiết bị này')
    expect(screen.getByRole('button', { name: /Đăng xuất mọi thiết bị khác/ })).toBeDisabled()
  })

  it('does not count dead sessions as "others" to log out', async () => {
    mockSessions([
      makeSession({ id: 1, is_current: true }),
      makeSession({ id: 2, is_alive: false, ending: 'Đã đăng xuất' }),
    ])
    renderTab()
    await screen.findByText('Đã đăng xuất')
    expect(screen.getByRole('button', { name: /Đăng xuất mọi thiết bị khác/ })).toBeDisabled()
    expect(screen.queryByRole('button', { name: /^Đăng xuất$/ })).not.toBeInTheDocument()
  })

  it('logs out every other device through revoke-others', async () => {
    mockSessions([makeSession({ id: 1, is_current: true }), makeSession({ id: 2 })])
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: /Đăng xuất mọi thiết bị khác/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/auth/sessions/revoke-others', {}))
  })

  it('shows an empty state instead of a blank list', async () => {
    mockSessions([], 0)
    renderTab()
    expect(await screen.findByText(/Không có thiết bị nào khác/)).toBeInTheDocument()
  })
})
