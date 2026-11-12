import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ConcurrentMember, ConcurrentMembersResult } from '../types/concurrent-member'
import { DepartmentConcurrentMembersTable } from './department-concurrent-members-table'

const state = vi.hoisted(() => ({
  canRead: true,
  result: undefined as ConcurrentMembersResult | undefined,
  isLoading: false,
  isError: false,
  lastCall: undefined as { params: unknown; enabled: boolean | undefined } | undefined,
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => state.canRead }),
}))

vi.mock('../hooks/use-concurrent-members', () => ({
  useConcurrentMembers: (params: unknown, options: { enabled?: boolean }) => {
    state.lastCall = { params, enabled: options.enabled }
    return { data: state.result, isLoading: state.isLoading, isError: state.isError }
  },
}))

function member(over: Partial<ConcurrentMember> = {}): ConcurrentMember {
  return {
    id: 1,
    employee_id: 11,
    code: 'NSU011',
    full_name: 'Lê Văn Kiêm',
    position_label: 'Phó phòng',
    company_id: 2,
    company_name: 'Công ty B',
    department_id: 7,
    department_name: 'Phòng Kế toán',
    from_date: '2026-09-01',
    to_date: null,
    status: 2,
    status_label: 'Đang hiệu lực',
    counts_scope: true,
    primary_company_id: 1,
    primary_company_name: 'Công ty A',
    primary_department_id: 3,
    primary_department_name: 'Phòng Thu mua',
    can_open: true,
    ...over,
  }
}

function renderTable() {
  //  `DataTable` đọc `useQueryClient` cho nút Tải lại, nên cần provider dù hook dữ liệu đã bị giả.
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <DepartmentConcurrentMembersTable departmentId={7} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('DepartmentConcurrentMembersTable', () => {
  beforeEach(() => {
    state.canRead = true
    state.result = { items: [member()], total: 1, truncated: false }
    state.isLoading = false
    state.isError = false
    state.lastCall = undefined
  })

  it('shows the concurrent person with the Kiêm nhiệm badge, their concurrent role, company and primary place', () => {
    renderTable()
    expect(screen.getByText('Kiêm nhiệm tại phòng này (1)')).toBeInTheDocument()
    expect(screen.getByText('Kiêm nhiệm')).toBeInTheDocument()
    expect(screen.getByText('Phó phòng')).toBeInTheDocument()
    expect(screen.getByText('Công ty B')).toBeInTheDocument()
    expect(screen.getByText('Phòng Thu mua — Công ty A')).toBeInTheDocument()
    expect(screen.getByText('Từ 01/09/2026')).toBeInTheDocument()
  })

  it('links the name to the profile only when the profile can be opened', () => {
    state.result = {
      items: [member(), member({ id: 2, employee_id: 12, code: 'NSU012', full_name: 'Chỉ Xem Tên', can_open: false })],
      total: 2,
      truncated: false,
    }
    renderTable()
    expect(screen.getByRole('link', { name: 'Lê Văn Kiêm' })).toHaveAttribute('href', '/hr/employees/11')
    expect(screen.getByText('Chỉ Xem Tên')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Chỉ Xem Tên' })).not.toBeInTheDocument()
  })

  it('flags rows that are not in effect yet with their own status badge', () => {
    state.result = { items: [member({ status: 1, status_label: 'Sắp tới' })], total: 1, truncated: false }
    renderTable()
    expect(screen.getByText('Sắp tới')).toBeInTheDocument()
  })

  it('renders nothing when nobody is concurrent here, so ordinary departments stay uncluttered', () => {
    state.result = { items: [], total: 0, truncated: false }
    const { container } = renderTable()
    expect(container).toBeEmptyDOMElement()
  })

  it('does not call the API and renders nothing without employee.read', () => {
    state.canRead = false
    const { container } = renderTable()
    expect(container).toBeEmptyDOMElement()
    expect(state.lastCall?.enabled).toBe(false)
  })

  it('keeps the card visible with an error message when the load fails instead of vanishing silently', () => {
    state.result = undefined
    state.isError = true
    renderTable()
    expect(screen.getByText('Không tải được danh sách kiêm nhiệm.')).toBeInTheDocument()
  })

  it('warns that the list was cut when the backend reports truncation', () => {
    state.result = { items: [member()], total: 200, truncated: true }
    renderTable()
    expect(screen.getByText(/chỉ hiện 200 người đầu/)).toBeInTheDocument()
  })

  it('passes the department id to the hook (hook is the only thing that talks to the API)', () => {
    renderTable()
    expect(state.lastCall?.params).toEqual({ department_id: 7 })
  })
})
