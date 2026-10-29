import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { MonthlyReminders } from '../types/monthly-reminders'
import { MonthlyRemindersCard } from './monthly-reminders-card'

//  Chặn ở tầng `@/core/api` theo luật test của dự án, không chặn axios.
const apiGet = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
  downloadFile: vi.fn(),
}))

const TODAY = new Date(2026, 9, 28)

function build() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <MonthlyRemindersCard today={TODAY} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function group<T>(items: T[], allowed = true) {
  return { allowed, items, total: items.length, truncated: false }
}

const DENIED = group([], false)

function reply(data: Partial<MonthlyReminders>) {
  apiGet.mockResolvedValue({
    month: '2026-10',
    birthdays: DENIED,
    anniversaries: DENIED,
    contracts: DENIED,
    probations: DENIED,
    ...data,
  })
}

beforeEach(() => {
  apiGet.mockReset()
})

describe('MonthlyRemindersCard', () => {
  it('asks for the current month on open', async () => {
    reply({ birthdays: group([]), anniversaries: group([]), contracts: group([]), probations: group([]) })
    build()
    await screen.findByText('Sinh nhật')
    expect(apiGet).toHaveBeenCalledWith('/api/employees/monthly-reminders', { params: { month: '2026-10' } })
  })

  it('hides groups the backend left out for lack of permission', async () => {
    //  Không có `employee_sensitive.read` / `labor_contract.read` → backend trả `allowed: false`.
    reply({ anniversaries: group([]) })
    build()
    expect(await screen.findByText('Kỷ niệm năm làm việc')).toBeInTheDocument()
    expect(screen.queryByText('Sinh nhật')).not.toBeInTheDocument()
    expect(screen.queryByText('HĐ / thử việc hết hạn')).not.toBeInTheDocument()
  })

  it('says the viewer lacks permission when every group is missing, not "nobody"', async () => {
    reply({})
    build()
    expect(await screen.findByText(/chưa có quyền xem mục nhắc nào/)).toBeInTheDocument()
    expect(screen.queryByText('Không có ai trong tháng này.')).not.toBeInTheDocument()
  })

  it('links each row to the employee profile, contracts straight to the contract tab', async () => {
    reply({
      birthdays: group([{ employee_id: 7, employee_name: 'Trần Thị B', employee_code: 'NV07', day: 5, month: 10 }]),
      contracts: group([]),
      probations: group([
        {
          employee_id: 9,
          employee_code: 'NV09',
          employee_name: 'Lê Văn C',
          contract_code: 'HDTV09',
          contract_no: '',
          end_date: '2026-10-20',
          days_left: 22,
          level: 'warn',
        },
      ]),
    })
    build()
    const birthday = await screen.findByRole('link', { name: /Trần Thị B/ })
    expect(birthday).toHaveAttribute('href', '/hr/employees/7')
    expect(within(birthday).getByText(/Sinh nhật 05\/10/)).toBeInTheDocument()
    const probation = screen.getByRole('link', { name: /Lê Văn C/ })
    expect(probation).toHaveAttribute('href', '/hr/employees/9?tab=labor-contracts')
    expect(within(probation).getByText(/Thử việc hết hạn 20\/10/)).toBeInTheDocument()
  })

  it('shows an honest error instead of "nobody" when loading fails', async () => {
    apiGet.mockRejectedValue(new Error('boom'))
    build()
    expect(await screen.findByText(/Không tải được lịch nhắc/)).toBeInTheDocument()
  })

  it('moves to the previous and next month', async () => {
    reply({ birthdays: group([]) })
    build()
    await screen.findByText('Sinh nhật')
    fireEvent.click(screen.getByRole('button', { name: 'Tháng trước' }))
    await screen.findByText('Tháng 9/2026')
    expect(apiGet).toHaveBeenLastCalledWith('/api/employees/monthly-reminders', { params: { month: '2026-09' } })
    fireEvent.click(screen.getByRole('button', { name: 'Tháng sau' }))
    fireEvent.click(screen.getByRole('button', { name: 'Tháng sau' }))
    await screen.findByText('Tháng 11/2026')
    expect(apiGet).toHaveBeenLastCalledWith('/api/employees/monthly-reminders', { params: { month: '2026-11' } })
  })
})

describe('MonthlyRemindersCard — contract lookahead', () => {
  it('warns that a far month may be missing contracts instead of claiming nobody', async () => {
    reply({ contracts: group([]), probations: group([]) })
    build()
    await screen.findByText('HĐ / thử việc hết hạn')
    expect(screen.queryByText(/180 ngày tới/)).not.toBeInTheDocument()
    for (let i = 0; i < 7; i += 1) fireEvent.click(screen.getByRole('button', { name: 'Tháng sau' }))
    await screen.findByText('Tháng 5/2027')
    expect(await screen.findByText(/180 ngày tới/)).toBeInTheDocument()
  })
})
