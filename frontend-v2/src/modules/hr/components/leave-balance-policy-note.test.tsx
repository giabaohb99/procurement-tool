import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'
import { LeaveBalancePolicyNote } from './leave-balance-policy-note'

const apiGet = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  extractErrorMessage: () => 'lỗi',
  httpClient: {},
}))

let granted = new Set<string>()
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.has(`${entity}.${action}`) }),
}))

const ACTIVE = {
  id: 7,
  employee_id: 11,
  policy_id: 4,
  policy_name: 'Cấp quản lý',
  effective_from: '2026-07-01',
  effective_to: null,
  state: 2,
}

let assignments: unknown[] = [ACTIVE]

/** "Hôm nay" cố định 03/11/2026 (giờ VN) — năm hiện tại là 2026. */
const THIS_YEAR = 2026

function renderNote(leaveTypeId = 1, year = THIS_YEAR) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <LeaveBalancePolicyNote employeeId={11} leaveTypeId={leaveTypeId} year={year} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  //  Chỉ giả `Date` — giả cả bộ hẹn giờ thì TanStack Query treo.
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date('2026-11-03T09:00:00+07:00'))
  granted = new Set(['leave_balance.read', 'leave_type.read', 'leave_type.write'])
  assignments = [ACTIVE]
  apiGet.mockReset().mockImplementation((url: string) =>
    Promise.resolve(
      url === '/api/leave-policy-assignments'
        ? { total: assignments.length, items: assignments }
        : { total: 1, items: [{ id: 1, leave_type_id: 1, annual_days: 15 }] },
    ),
  )
})

afterEach(() => {
  vi.useRealTimers()
})

describe('LeaveBalancePolicyNote (duoc-CR-717)', () => {
  it('names the policy active today, links to it, and says how many days it grants for this leave type', async () => {
    renderNote(1)
    expect(await screen.findByText(/Chính sách đang áp hôm nay/)).toBeInTheDocument()
    const link = await screen.findByRole('link', { name: 'Cấp quản lý' })
    expect(link).toHaveAttribute('href', appRoutes.hr.leavePolicyDetail(4))
    expect(await screen.findByText(/khai 15 ngày\/năm cho loại nghỉ này/)).toBeInTheDocument()
    expect(screen.getByText(/01\/07\/2026 → Không thời hạn/)).toBeInTheDocument()
    expect(apiGet).toHaveBeenCalledWith(
      '/api/leave-policy-assignments',
      expect.objectContaining({
        params: expect.objectContaining({ employee_id: 11, page_size: 1, active_on: '2026-11-03' }),
      }),
    )
  })

  it('says the leave type falls back to its own quota when the policy does not list it (D1a)', async () => {
    renderNote(99)
    expect(await screen.findByText(/không khai loại nghỉ này nên vẫn theo hạn mức của loại nghỉ/)).toBeInTheDocument()
  })

  it('says "theo hạn mức của loại nghỉ" when no policy is active today', async () => {
    assignments = []
    renderNote()
    expect(await screen.findByText(/Hôm nay không có chính sách nghỉ phép nào đang áp/)).toBeInTheDocument()
  })

  it('renders nothing and calls nothing without leave_balance.read', async () => {
    granted = new Set(['leave_type.read'])
    renderNote()
    await waitFor(() => expect(apiGet).not.toHaveBeenCalled())
    expect(screen.queryByText(/Chính sách/)).not.toBeInTheDocument()
  })

  it('with leave_type.read but no manage right shows the name as plain text, not a link that 403s (review M2)', async () => {
    //  LỖI REVIEW M2: liên kết hiện với `leave_type.read`, mà route chi tiết gói gác quyền QUẢN LÝ → 403.
    granted = new Set(['leave_balance.read', 'leave_type.read'])
    renderNote()
    expect(await screen.findByText('Cấp quản lý')).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
    //  Vẫn đọc được dòng gói nên câu "khai … ngày" vẫn có.
    expect(await screen.findByText(/khai 15 ngày\/năm/)).toBeInTheDocument()
  })

  it.each([2025, 2027])(
    'renders nothing and calls nothing for a balance of another year (%i) — it would explain the wrong year (review M1)',
    async (year) => {
      renderNote(1, year)
      await waitFor(() => expect(apiGet).not.toHaveBeenCalled())
      expect(screen.queryByText(/Chính sách/)).not.toBeInTheDocument()
    },
  )

  it('uses the Vietnam date for "this year": 31/12 at 23:30 UTC is already next year in VN', async () => {
    vi.setSystemTime(new Date('2026-12-31T23:30:00Z'))
    renderNote(1, 2027)
    expect(await screen.findByText(/Chính sách đang áp hôm nay/)).toBeInTheDocument()
  })

  it('renders nothing when the assignment lookup fails, instead of claiming no policy applies (review M1)', async () => {
    apiGet.mockImplementation((url: string) =>
      url === '/api/leave-policy-assignments' ? Promise.reject(new Error('500')) : Promise.resolve({ total: 0, items: [] }),
    )
    renderNote()
    await waitFor(() => expect(apiGet).toHaveBeenCalled())
    await new Promise((r) => setTimeout(r, 0))
    expect(screen.queryByText(/không có chính sách/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Chính sách/)).not.toBeInTheDocument()
  })

  it('without leave_type.read shows the name as plain text and skips the policy lines call', async () => {
    granted = new Set(['leave_balance.read'])
    renderNote()
    expect(await screen.findByText('Cấp quản lý')).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalledWith('/api/leave-policies/4/lines', expect.anything())
    expect(apiGet).not.toHaveBeenCalledWith('/api/leave-policies/4/lines')
  })
})
