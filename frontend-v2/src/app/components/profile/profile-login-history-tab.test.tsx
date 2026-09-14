import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type {
  LoginHistoryItem,
  LoginHistoryResult,
  LoginSessionItem,
  MySessionsResult,
} from '@/modules/system/api/login-session-api'
import { HISTORY_KIND } from '@/modules/system/api/login-session-api'
import { ProfileLoginHistoryTab } from './profile-login-history-tab'

/**
 * Tab «Lịch sử đăng nhập» ở Trang cá nhân (bao-CR-400).
 *
 * Hai chỗ dễ lủng:
 * 1. Phải gọi cửa TỰ THÂN `/api/auth/sessions/history`, không phải cửa quản trị
 *    `/api/login-sessions/history` — cửa đó đòi khóa `login_session.read`, người
 *    thường mở tab là ăn 403.
 * 2. Số «Phiên đang mở» lấy từ `alive_count` backend đếm, KHÔNG đếm số dòng
 *    trả về — danh sách bị cắt trang hoặc lẫn phiên chết thì đếm dòng là sai.
 */

const apiGet = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

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
    is_current: true,
    ...overrides,
  }
}

function makeRow(overrides: Partial<LoginHistoryItem> = {}): LoginHistoryItem {
  return {
    kind: HISTORY_KIND.LOGIN,
    ok: true,
    at: '2026-09-14T08:00:00',
    session_id: 1,
    login_method: 1,
    login_method_label: 'Mật khẩu',
    device_label: 'Chrome trên Windows',
    ip: '10.0.0.1',
    ending: 'Còn hiệu lực',
    revoked_by_name: '',
    message: '',
    ...overrides,
  }
}

let sessionsResult: MySessionsResult
let historyResult: LoginHistoryResult

function routeApiGet(url: string, opts?: { params?: { days?: number } }) {
  if (url === '/api/auth/sessions') return Promise.resolve(sessionsResult)
  if (url === '/api/auth/sessions/history') {
    return Promise.resolve({ ...historyResult, days: opts?.params?.days ?? historyResult.days })
  }
  return Promise.reject(new Error(`unexpected GET ${url}`))
}

function renderTab() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ProfileLoginHistoryTab />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProfileLoginHistoryTab', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiGet.mockImplementation(routeApiGet)
    // Danh sách chỉ có MỘT dòng nhưng backend nói còn BA phiên sống.
    sessionsResult = { items: [makeSession()], current_session_id: 1, alive_count: 3 }
    historyResult = {
      items: [
        makeRow(),
        makeRow({
          kind: HISTORY_KIND.LOGIN_FAILED,
          ok: false,
          session_id: 0,
          device_label: '',
          ip: '1.2.3.4',
          ending: '',
          message: '',
        }),
      ],
      days: 90,
      login_count: 1,
      failed_count: 1,
    }
  })

  it('reads the self-service history endpoint with the default 90-day range', async () => {
    renderTab()
    await screen.findByText('Chrome trên Windows')
    expect(apiGet).toHaveBeenCalledWith('/api/auth/sessions/history', { params: { days: 90 } })
    expect(apiGet).toHaveBeenCalledWith('/api/auth/sessions', { params: { active_only: true } })
    expect(apiGet).not.toHaveBeenCalledWith('/api/login-sessions/history', expect.anything())
  })

  it('shows the alive count reported by the backend, not the number of rows', async () => {
    renderTab()
    const tile = (await screen.findByText('Phiên đang mở')).parentElement
    expect(tile).not.toBeNull()
    await waitFor(() => expect(tile).toHaveTextContent('3'))
    expect(screen.getByRole('link', { name: 'Xem thiết bị' })).toHaveAttribute(
      'href',
      '/me?tab=devices',
    )
  })

  it('surfaces failed attempts with a warning and the password fallback text', async () => {
    renderTab()
    expect(await screen.findByText('Thất bại')).toBeInTheDocument()
    expect(screen.getByText('Sai mật khẩu')).toBeInTheDocument()
    expect(screen.getByText(/Có người gõ sai mật khẩu/)).toBeInTheDocument()
  })

  it('does not nag about failed attempts when there are none', async () => {
    historyResult = { items: [makeRow()], days: 90, login_count: 1, failed_count: 0 }
    renderTab()
    await screen.findByText('Chrome trên Windows')
    expect(screen.queryByText(/Có người gõ sai mật khẩu/)).not.toBeInTheDocument()
  })

  it('refetches with the chosen range when a range button is pressed', async () => {
    renderTab()
    await screen.findByText('Chrome trên Windows')
    expect(screen.getByRole('button', { name: '90 ngày' })).toHaveAttribute('aria-pressed', 'true')

    await userEvent.click(screen.getByRole('button', { name: '30 ngày' }))
    await waitFor(() =>
      expect(apiGet).toHaveBeenCalledWith('/api/auth/sessions/history', { params: { days: 30 } }),
    )
    expect(screen.getByRole('button', { name: '30 ngày' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '90 ngày' })).toHaveAttribute('aria-pressed', 'false')
    expect(await screen.findByText('Lần đăng nhập · 30 ngày')).toBeInTheDocument()
  })

  it('shows an empty state instead of a blank list', async () => {
    historyResult = { items: [], days: 90, login_count: 0, failed_count: 0 }
    renderTab()
    expect(
      await screen.findByText('Chưa ghi nhận lần đăng nhập nào trong 90 ngày qua.'),
    ).toBeInTheDocument()
  })
})
