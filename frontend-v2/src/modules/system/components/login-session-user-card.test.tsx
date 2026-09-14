import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ComponentProps } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { LoginHistoryResult, LoginSessionItem, LoginSessionListResult } from '../api/login-session-api'
import { HISTORY_KIND } from '../api/login-session-api'
import { LoginSessionUserCard } from './login-session-user-card'

/**
 * Thẻ «Phiên đăng nhập» ở tab Tài khoản của hồ sơ nhân sự (bao-CR-395).
 *
 * Ba chỗ dễ lủng:
 * 1. Thẻ mượn dữ liệu của phân hệ Quản trị — thiếu `login_session.read` thì
 *    KHÔNG được gọi API (mount là gọi → toast 403 ngay khi mở tab, xem CLAUDE.md
 *    mục tab Nhà cung cấp).
 * 2. Nút «Khóa tài khoản» đi qua `PUT /api/users/{id}/active` nên gác bằng
 *    `user.write`, không phải `login_session.delete` — hai khóa khác nhau.
 * 3. Đá phiên phải gọi đúng cửa quản trị `/api/login-sessions/{id}/revoke`,
 *    không phải cửa tự phục vụ `/api/auth/sessions/{id}/revoke` (cửa đó chỉ đá
 *    được phiên của CHÍNH MÌNH, gọi nhầm là 404 mà không ai hiểu vì sao).
 */

let granted: string[] = []

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => granted.includes(`${entity}.${action}`),
    canAny: () => true,
    canAccess: () => true,
  }),
}))

const apiGet = vi.fn()
const apiPost = vi.fn()
const httpPut = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: { put: (...args: unknown[]) => httpPut(...args) },
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

// Hộp xác nhận toàn cục: coi như người dùng luôn bấm Đồng ý.
vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: vi.fn(() => Promise.resolve(true)),
}))

function makeSession(overrides: Partial<LoginSessionItem> = {}): LoginSessionItem {
  return {
    id: 11,
    user_id: 7,
    user_name: 'Nguyễn Văn A',
    ip: '10.0.0.5',
    last_seen_ip: '10.0.0.5',
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

const sessionsResult: LoginSessionListResult = {
  items: [makeSession()],
  total: 1,
  page: 1,
  page_size: 50,
}

const historyResult: LoginHistoryResult = {
  items: [
    {
      kind: HISTORY_KIND.LOGIN,
      ok: true,
      at: '2026-09-14T08:00:00',
      session_id: 11,
      login_method: 1,
      login_method_label: 'Mật khẩu',
      device_label: 'Chrome trên Windows',
      ip: '10.0.0.5',
      ending: 'Còn hiệu lực',
      revoked_by_name: '',
      message: '',
    },
    {
      kind: HISTORY_KIND.LOGIN_FAILED,
      ok: false,
      at: '2026-09-13T22:00:00',
      session_id: 0,
      login_method: 1,
      login_method_label: 'Mật khẩu',
      device_label: '',
      ip: '1.2.3.4',
      ending: '',
      revoked_by_name: '',
      message: 'Sai mật khẩu',
    },
  ],
  days: 90,
  login_count: 1,
  failed_count: 1,
}

function routeApiGet(url: string) {
  if (url === '/api/login-sessions/history') return Promise.resolve(historyResult)
  if (url === '/api/login-sessions') return Promise.resolve(sessionsResult)
  // `/api/users?employee_id=…` — tài khoản gắn với nhân sự, đang mở.
  return Promise.resolve({ items: [{ id: 7, is_active: true }], total: 1, page: 1, page_size: 1 })
}

function renderCard(props: Partial<ComponentProps<typeof LoginSessionUserCard>> = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <LoginSessionUserCard employeeId={3} userId={7} userName="Nguyễn Văn A" {...props} />
    </QueryClientProvider>,
  )
}

describe('LoginSessionUserCard', () => {
  beforeEach(() => {
    granted = ['login_session.read', 'login_session.delete', 'user.read', 'user.write']
    apiGet.mockReset()
    apiPost.mockReset()
    httpPut.mockReset()
    apiGet.mockImplementation(routeApiGet)
    apiPost.mockResolvedValue(null)
    httpPut.mockResolvedValue({ data: { success: true, data: null } })
  })

  it('renders nothing and calls no API without login_session.read', () => {
    granted = ['user.read', 'user.write']
    const { container } = renderCard()
    expect(container).toBeEmptyDOMElement()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('renders nothing for an employee without a login account (userId = 0)', () => {
    const { container } = renderCard({ userId: 0 })
    expect(container).toBeEmptyDOMElement()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('lists open sessions and the 90-day summary', async () => {
    renderCard()
    expect(await screen.findByText('1 lần đăng nhập · 1 lần thất bại')).toBeInTheDocument()
    // Nhãn máy hiện HAI lần: một ở phiên đang mở, một ở dòng lịch sử đăng nhập.
    expect(screen.getAllByText('Chrome trên Windows')).toHaveLength(2)
    expect(screen.getByText('Thất bại')).toBeInTheDocument()
    expect(screen.getByText('Sai mật khẩu')).toBeInTheDocument()
  })

  it('hides the kick buttons without login_session.delete', async () => {
    granted = ['login_session.read', 'user.read']
    renderCard()
    await screen.findByText('1 lần đăng nhập · 1 lần thất bại')
    expect(screen.queryByRole('button', { name: /Đá phiên/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Bắt đăng nhập lại/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Khóa tài khoản/ })).not.toBeInTheDocument()
  })

  it('gates the lock button on user.write, not on login_session.delete', async () => {
    granted = ['login_session.read', 'login_session.delete', 'user.read']
    renderCard()
    expect(await screen.findByRole('button', { name: /Bắt đăng nhập lại/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Khóa tài khoản/ })).not.toBeInTheDocument()
  })

  it('kicks a single session through the admin endpoint', async () => {
    renderCard()
    await userEvent.click(await screen.findByRole('button', { name: /Đá phiên/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/login-sessions/11/revoke', {}))
  })

  it('forces re-login through the per-user logout-all endpoint', async () => {
    renderCard()
    await userEvent.click(await screen.findByRole('button', { name: /Bắt đăng nhập lại/ }))
    await waitFor(() =>
      expect(apiPost).toHaveBeenCalledWith('/api/login-sessions/users/7/logout-all', {}),
    )
  })

  it('locks the account via PUT /api/users/{id}/active with is_active=false', async () => {
    renderCard()
    await userEvent.click(await screen.findByRole('button', { name: /Khóa tài khoản/ }))
    await waitFor(() =>
      expect(httpPut).toHaveBeenCalledWith('/api/users/7/active', { is_active: false }),
    )
  })

  it('hides the lock button when the account is already locked', async () => {
    apiGet.mockImplementation((url: string) => {
      if (url === '/api/login-sessions/history') return Promise.resolve(historyResult)
      if (url === '/api/login-sessions') return Promise.resolve(sessionsResult)
      return Promise.resolve({ items: [{ id: 7, is_active: false }], total: 1, page: 1, page_size: 1 })
    })
    renderCard()
    await screen.findByText('1 lần đăng nhập · 1 lần thất bại')
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /Khóa tài khoản/ })).not.toBeInTheDocument(),
    )
  })
})
