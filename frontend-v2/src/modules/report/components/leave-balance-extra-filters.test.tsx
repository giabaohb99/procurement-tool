import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { apiGet } from '@/core/api'
import type * as CoreApiModule from '@/core/api'

import { LeaveBalanceExtraFilters } from './leave-balance-extra-filters'
import { ReportDepartmentFilter } from './report-department-filter'

vi.mock('@/core/api', async (importOriginal) => {
  const actual = await importOriginal<typeof CoreApiModule>()
  return { ...actual, apiGet: vi.fn() }
})

let canReadDepartment = true
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => entity === 'department' && action === 'read' && canReadDepartment,
  }),
}))

function SearchProbe() {
  return <p data-testid="search">{useLocation().search}</p>
}

function renderWithUrl(ui: ReactNode, url = '/report/leave-balance') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        {ui}
        <SearchProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  canReadDepartment = true
  vi.mocked(apiGet).mockReset()
  vi.mocked(apiGet).mockResolvedValue({ items: [{ id: 7, name: 'Kế toán' }], total: 1 })
})

describe('ReportDepartmentFilter', () => {
  it('is hidden and never loads departments without department.read', () => {
    canReadDepartment = false
    renderWithUrl(<ReportDepartmentFilter />)
    expect(screen.queryByRole('combobox', { name: 'Phòng ban' })).not.toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('writes department_id to the URL and removes it again on "Tất cả phòng ban"', async () => {
    const user = userEvent.setup()
    renderWithUrl(<ReportDepartmentFilter />)
    await user.click(screen.getByRole('combobox', { name: 'Phòng ban' }))
    await user.click(await screen.findByRole('option', { name: 'Kế toán' }))
    expect(screen.getByTestId('search')).toHaveTextContent('?department_id=7')

    await user.click(screen.getByRole('combobox', { name: 'Phòng ban' }))
    await user.click(screen.getByRole('option', { name: 'Tất cả phòng ban' }))
    await waitFor(() => expect(screen.getByTestId('search')).toBeEmptyDOMElement())
  })
})

describe('LeaveBalanceExtraFilters — employee_status', () => {
  it('shows "Đang làm" by default without writing it to the URL', () => {
    renderWithUrl(<LeaveBalanceExtraFilters />)
    expect(screen.getByRole('combobox', { name: 'Trạng thái nhân sự' })).toHaveTextContent('Đang làm')
    expect(screen.getByTestId('search')).toBeEmptyDOMElement()
    //  Hai ô cùng một hàng: phòng ban + trạng thái.
    expect(screen.getByRole('combobox', { name: 'Phòng ban' })).toBeInTheDocument()
  })

  it('writes resigned / all, and clears the param when going back to "Đang làm"', async () => {
    const user = userEvent.setup()
    renderWithUrl(<LeaveBalanceExtraFilters />)
    const trigger = screen.getByRole('combobox', { name: 'Trạng thái nhân sự' })

    await user.click(trigger)
    await user.click(screen.getByRole('option', { name: 'Đã nghỉ' }))
    expect(screen.getByTestId('search')).toHaveTextContent('?employee_status=resigned')

    await user.click(trigger)
    await user.click(screen.getByRole('option', { name: 'Tất cả nhân sự' }))
    expect(screen.getByTestId('search')).toHaveTextContent('?employee_status=all')

    await user.click(trigger)
    await user.click(screen.getByRole('option', { name: 'Đang làm' }))
    await waitFor(() => expect(screen.getByTestId('search')).toBeEmptyDOMElement())
  })

  it('shows the default for a hand-typed unknown value instead of a blank select', () => {
    renderWithUrl(<LeaveBalanceExtraFilters />, '/report/leave-balance?employee_status=xyz')
    expect(screen.getByRole('combobox', { name: 'Trạng thái nhân sự' })).toHaveTextContent('Đang làm')
  })
})
