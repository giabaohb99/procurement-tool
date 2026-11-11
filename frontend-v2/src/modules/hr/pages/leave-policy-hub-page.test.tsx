import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import { appRoutes } from '@/shared/constants/app-routes'
import { LeavePoliciesLegacyRedirect } from './leave-policies-legacy-redirect'
import { LeavePolicyHubPage } from './leave-policy-hub-page'

const apiGet = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiDelete: vi.fn(),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  extractErrorMessage: () => 'lỗi',
  httpClient: {},
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

let granted = new Set<string>()
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.has(`${entity}.${action}`) }),
}))

const POLICIES = { total: 1, items: [{ id: 4, code: 'CS-QL', name: 'Cấp quản lý', note: '', is_active: true }] }
const ASSIGNMENTS = {
  total: 1,
  items: [
    {
      id: 7,
      employee_id: 11,
      company_id: 1,
      policy_id: 4,
      effective_from: '2026-01-01',
      effective_to: null,
      note: '',
      employee_name: 'Trần An',
      employee_code: 'NSU011',
      policy_name: 'Cấp quản lý',
      state: 2,
    },
  ],
}

/** Hiện đường dẫn đang đứng để kiểm chuyển hướng. */
function LocationProbe() {
  const { pathname, search } = useLocation()
  return <output aria-label="location">{`${pathname}${search}`}</output>
}

function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path={appRoutes.hr.leavePolicyAssignments} element={<LeavePolicyHubPage />} />
          <Route path={appRoutes.hr.leavePolicies} element={<LeavePoliciesLegacyRedirect />} />
        </Routes>
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

const tabLinks = () => screen.getAllByRole('link').filter((a) => a.closest('nav[aria-label="Chính sách nghỉ phép"]'))
const activeTab = () => tabLinks().find((a) => a.getAttribute('aria-current') === 'page')?.textContent
const calledUrls = () => apiGet.mock.calls.map(([url]) => url as string)

beforeEach(() => {
  useAuthStore.setState({ user: null })
  granted = new Set()
  apiGet.mockReset().mockImplementation((url: string) =>
    Promise.resolve(
      url === '/api/leave-policy-assignments'
        ? ASSIGNMENTS
        : url === '/api/leave-policies'
          ? POLICIES
          : { total: 0, items: [] },
    ),
  )
})

describe('LeavePolicyHubPage (duoc-CR-750)', () => {
  it('opens the Phân bổ tab by default for someone who can do both, with its own header buttons', async () => {
    granted = new Set(['leave_balance.read', 'leave_balance.write', 'leave_type.read', 'leave_type.write', 'leave_type.create'])
    renderAt(appRoutes.hr.leavePolicyAssignments)
    expect(await screen.findByText('Trần An')).toBeInTheDocument()
    expect(tabLinks().map((a) => a.textContent)).toEqual(['Phân bổ', 'Chính sách'])
    expect(activeTab()).toBe('Phân bổ')
    expect(screen.getByRole('button', { name: 'Phân bổ' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Phân bổ hàng loạt' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Thêm chính sách/ })).not.toBeInTheDocument()
  })

  it('switches to Chính sách: header now offers Thêm chính sách, assignment buttons are gone, old filters dropped', async () => {
    granted = new Set(['leave_balance.read', 'leave_balance.write', 'leave_type.read', 'leave_type.write', 'leave_type.create'])
    const user = userEvent.setup()
    renderAt(`${appRoutes.hr.leavePolicyAssignments}?policy_id=4&q=NSU011`)
    await screen.findByText('Trần An')

    await user.click(screen.getByRole('link', { name: 'Chính sách' }))
    expect(await screen.findByText('Cấp quản lý', { selector: 'span' })).toBeInTheDocument()
    expect(activeTab()).toBe('Chính sách')
    expect(screen.getByRole('button', { name: /Thêm chính sách/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Phân bổ hàng loạt' })).not.toBeInTheDocument()
    //  Bộ lọc của bảng phân bổ không dính sang bảng gói.
    expect(screen.getByLabelText('location')).toHaveTextContent(/^\/hr\/leave-policy-assignments\?tab=policies$/)
  })

  it('a policy-only writer lands on Chính sách and never loads assignments, even when the URL asks for them', async () => {
    granted = new Set(['leave_type.read', 'leave_type.write'])
    renderAt(`${appRoutes.hr.leavePolicyAssignments}?tab=assignments`)
    expect(await screen.findByText('Cấp quản lý', { selector: 'span' })).toBeInTheDocument()
    expect(tabLinks().map((a) => a.textContent)).toEqual(['Chính sách'])
    expect(activeTab()).toBe('Chính sách')
    expect(calledUrls()).not.toContain('/api/leave-policy-assignments')
  })

  it('an assignment-only writer sees just the Phân bổ tab and never loads the policy CRUD list as a tab', async () => {
    granted = new Set(['leave_balance.read', 'leave_balance.write'])
    renderAt(`${appRoutes.hr.leavePolicyAssignments}?tab=policies`)
    expect(await screen.findByText('Trần An')).toBeInTheDocument()
    expect(tabLinks().map((a) => a.textContent)).toEqual(['Phân bổ'])
    expect(activeTab()).toBe('Phân bổ')
    expect(screen.queryByRole('button', { name: /Thêm chính sách/ })).not.toBeInTheDocument()
  })

  it('falls back to the first allowed tab on a garbage ?tab= value', async () => {
    granted = new Set(['leave_balance.read', 'leave_balance.write', 'leave_type.write'])
    renderAt(`${appRoutes.hr.leavePolicyAssignments}?tab=%3Cscript%3E`)
    expect(await screen.findByText('Trần An')).toBeInTheDocument()
    expect(activeTab()).toBe('Phân bổ')
  })

  it('shows 403 and calls no API for someone with read-only rights (route fence bypassed)', () => {
    granted = new Set(['leave_balance.read', 'leave_type.read'])
    renderAt(appRoutes.hr.leavePolicyAssignments)
    expect(screen.getByText('Không có quyền truy cập')).toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('redirects the old /hr/leave-policies link to the Chính sách tab and keeps its filters', async () => {
    granted = new Set(['leave_balance.write', 'leave_type.read', 'leave_type.write'])
    renderAt(`${appRoutes.hr.leavePolicies}?is_active=false&tab=assignments`)
    await waitFor(() =>
      expect(screen.getByLabelText('location')).toHaveTextContent(
        '/hr/leave-policy-assignments?tab=policies&is_active=false',
      ),
    )
    expect(activeTab()).toBe('Chính sách')
    await waitFor(() =>
      expect(apiGet).toHaveBeenCalledWith(
        '/api/leave-policies',
        expect.objectContaining({ params: expect.objectContaining({ is_active: 'false' }) }),
      ),
    )
  })
})
