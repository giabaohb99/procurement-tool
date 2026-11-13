import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ConcurrentMember, ConcurrentMembersResult } from '../types/concurrent-member'
import { CONCURRENT_KIND_COMPANY } from '../types/employee-concurrent'
import { CompanyConcurrentMembersTable } from './company-concurrent-members-table'

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
    kind: 2,
    kind_label: 'Công ty',
    code: 'NSU011',
    full_name: 'Lê Văn Kiêm',
    position_label: 'Phó phòng',
    company_id: 2,
    company_name: 'Công ty B',
    department_id: 0,
    department_name: '',
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
        <CompanyConcurrentMembersTable companyId={2} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('CompanyConcurrentMembersTable (duoc-CR-756)', () => {
  beforeEach(() => {
    state.canRead = true
    state.result = { items: [member()], total: 1, truncated: false }
    state.isLoading = false
    state.isError = false
    state.lastCall = undefined
  })

  it('asks for Công ty rows of THIS company only (company_id + kind=2), never by department', () => {
    renderTable()
    expect(state.lastCall?.params).toEqual({ company_id: 2, kind: CONCURRENT_KIND_COMPANY })
    expect(state.lastCall?.enabled).toBe(true)
  })

  it('shows code, name with the Kiêm nhiệm badge, concurrent role, period, status and the primary place', () => {
    renderTable()
    expect(screen.getByText('Kiêm nhiệm tại công ty này (1)')).toBeInTheDocument()
    for (const header of ['Mã NV', 'Họ tên', 'Chức vụ kiêm nhiệm', 'Thời hạn', 'Trạng thái', 'Nơi làm chính']) {
      expect(screen.getByRole('columnheader', { name: new RegExp(header) })).toBeInTheDocument()
    }
    expect(screen.getByText('NSU011')).toBeInTheDocument()
    expect(screen.getByText('Kiêm nhiệm')).toBeInTheDocument()
    expect(screen.getByText('Phó phòng')).toBeInTheDocument()
    expect(screen.getByText('Từ 01/09/2026')).toBeInTheDocument()
    expect(screen.getByText('Đang hiệu lực')).toBeInTheDocument()
    expect(screen.getByText('Phòng Thu mua — Công ty A')).toBeInTheDocument()
  })

  it('status lives in its own column — the name cell does not repeat it', () => {
    state.result = { items: [member({ status: 1, status_label: 'Sắp tới' })], total: 1, truncated: false }
    renderTable()
    expect(screen.getAllByText('Sắp tới')).toHaveLength(1)
  })

  it('links the name to the profile only when can_open', () => {
    state.result = {
      items: [member(), member({ id: 2, employee_id: 12, code: 'NSU012', full_name: 'Chỉ Xem Tên', can_open: false })],
      total: 2,
      truncated: false,
    }
    renderTable()
    expect(screen.getByRole('link', { name: 'Lê Văn Kiêm' })).toHaveAttribute('href', '/hr/employees/11')
    expect(screen.queryByRole('link', { name: 'Chỉ Xem Tên' })).not.toBeInTheDocument()
  })

  it('renders nothing when nobody is concurrent at this company', () => {
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

  it('keeps the card visible with an error message when the load fails', () => {
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
})
