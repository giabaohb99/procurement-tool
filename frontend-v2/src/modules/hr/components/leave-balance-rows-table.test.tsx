import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { LeaveBalance } from '../types/leave'
import { accrualFixture } from './leave-accrual-fixture'
import { balanceFixture } from './leave-balance-fixture'
import { LeaveBalanceRowsTable } from './leave-balance-rows-table'

const apiGet = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  downloadFile: vi.fn(),
  extractErrorMessage: () => 'lỗi',
  httpClient: {},
}))

let balances: LeaveBalance[] = []

function person(id: number, name: string, status: number): LeaveBalance {
  return balanceFixture({ id, employee_id: id, employee_name: name, ...accrualFixture(status) })
}

function Harness() {
  const search = useUrlSearchParam()
  return <LeaveBalanceRowsTable year="2026" onYearChange={() => {}} search={search} />
}

function renderTable() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/hr/leave-balances']}>
        <Harness />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  localStorage.clear()
  apiGet.mockReset().mockImplementation((url: string) =>
    Promise.resolve(
      url === '/api/leave-balances' ? { items: balances, total: balances.length } : { items: [], total: 0 },
    ),
  )
})

describe('LeaveBalanceRowsTable: missing-contract rule (duoc-CR-762 option B)', () => {
  it('<= half missing: amber label on the row, strip counts, no filter button', async () => {
    balances = [person(1, 'An', 3), person(2, 'Bình', 1), person(3, 'Chi', 1), person(4, 'Dũng', 2)]
    renderTable()
    await screen.findAllByText('Bình')
    expect(screen.getAllByText('Chưa có HĐLĐ trên hệ thống').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Đang thử việc — chưa tích').length).toBeGreaterThan(0)
    expect(screen.queryByRole('button', { name: 'Chỉ hiện người chưa đủ HĐLĐ' })).toBeNull()
  })

  it('> half missing: row labels hidden (probation kept), strip reads N/M and the filter narrows the list', async () => {
    //  3/5 — đúng nửa (2/4) vẫn còn nhãn, xem bài trong `leave-accrual-status.test.ts`. Mã 4 tính chung với mã 3.
    balances = [
      person(1, 'An', 3),
      person(2, 'Bình', 4),
      person(5, 'Cường', 3),
      person(3, 'Chi', 1),
      person(4, 'Dũng', 2),
    ]
    renderTable()
    await screen.findAllByText('Chi')
    expect(screen.queryByText('Chưa có HĐLĐ trên hệ thống')).toBeNull()
    expect(screen.queryByText(/Lịch sử HĐLĐ chưa đủ/)).toBeNull()
    expect(screen.getAllByText('Đang thử việc — chưa tích').length).toBeGreaterThan(0)
    expect(document.body.textContent).toContain('3/5 người chưa đủ HĐLĐ')

    await userEvent.click(screen.getByRole('button', { name: 'Chỉ hiện người chưa đủ HĐLĐ' }))
    expect(screen.getAllByText('An').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Bình').length).toBeGreaterThan(0)
    expect(screen.queryByText('Chi')).toBeNull()
    expect(screen.queryByText('Dũng')).toBeNull()

    await userEvent.click(screen.getByRole('button', { name: 'Hiện tất cả' }))
    expect(screen.getAllByText('Chi').length).toBeGreaterThan(0)
  })
})
