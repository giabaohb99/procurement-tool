import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { ExpiringLaborContract, ExpiringLaborContractList } from '../types/labor-contract'
import { ExpiringLaborContractsCard } from './expiring-labor-contracts-card'

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

function contract(over: Partial<ExpiringLaborContract>): ExpiringLaborContract {
  return {
    id: 1,
    code: 'HDLD001',
    contract_no: '',
    contract_type: 2,
    employee_id: 7,
    employee_code: 'NV07',
    employee_name: 'Trần Thị B',
    end_date: '2026-10-20',
    days_left: 4,
    level: 'danger',
    ...over,
  }
}

function list(items: ExpiringLaborContract[]): ExpiringLaborContractList {
  return {
    items,
    danger: items.filter((i) => i.level === 'danger').length,
    warn_days: 30,
    danger_days: 15,
  }
}

function build() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ExpiringLaborContractsCard />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset()
})

describe('ExpiringLaborContractsCard', () => {
  it('reads the scoped expiring endpoint, not the per-employee list', async () => {
    apiGet.mockResolvedValue(list([contract({})]))
    build()
    await screen.findByText('Trần Thị B')
    expect(apiGet).toHaveBeenCalledWith('/api/labor-contracts/expiring')
  })

  it('links each row straight to the contract tab of that employee', async () => {
    apiGet.mockResolvedValue(list([contract({ employee_id: 42 })]))
    build()
    const link = await screen.findByRole('link', { name: /Trần Thị B/ })
    expect(link).toHaveAttribute('href', '/hr/employees/42?tab=labor-contracts')
  })

  it('keeps the backend order and says overdue / today / days left in words', async () => {
    apiGet.mockResolvedValue(
      list([
        contract({ id: 1, employee_name: 'Quá hạn', days_left: -3 }),
        contract({ id: 2, employee_name: 'Hôm nay', days_left: 0 }),
        contract({ id: 3, employee_name: 'Còn xa', days_left: 22, level: 'warn' }),
      ]),
    )
    build()
    const links = await screen.findAllByRole('link')
    expect(links.map((l) => within(l).getByText(/Quá hạn \d|Hết hạn hôm nay|Còn \d/).textContent)).toEqual([
      'Quá hạn 3 ngày',
      'Hết hạn hôm nay',
      'Còn 22 ngày',
    ])
    expect(screen.getByText(/3 hợp đồng hết hạn trong 30 ngày tới hoặc đã quá hạn · 1 đã quá hạn/)).toBeInTheDocument()
  })

  it('prefers the printed contract number over the internal code, and never shows salary', async () => {
    apiGet.mockResolvedValue(list([contract({ contract_no: '15/2026/HĐLĐ' })]))
    build()
    expect(await screen.findByText(/15\/2026\/HĐLĐ · Xác định thời hạn · hết 20\/10\/2026/)).toBeInTheDocument()
    expect(screen.queryByText(/HDLD001/)).not.toBeInTheDocument()
    expect(screen.queryByText(/lương/i)).not.toBeInTheDocument()
  })

  //  Rà soát M2: thẻ cảnh báo tải hỏng mà nói «không có hợp đồng nào» là trấn an giả.
  it('says the list failed to load instead of claiming nothing is expiring', async () => {
    apiGet.mockRejectedValue(new Error('500'))
    build()
    expect(await screen.findByText(/Không tải được danh sách hợp đồng sắp hết hạn/)).toBeInTheDocument()
    expect(screen.queryByText(/Không có hợp đồng nào hết hạn/)).not.toBeInTheDocument()
    expect(screen.queryByText('Chưa có hợp đồng nào cần gia hạn.')).not.toBeInTheDocument()
  })

  it('says plainly when nothing needs renewing instead of drawing an empty box', async () => {
    apiGet.mockResolvedValue(list([]))
    build()
    expect(await screen.findByText('Chưa có hợp đồng nào cần gia hạn.')).toBeInTheDocument()
    expect(screen.getByText('Không có hợp đồng nào hết hạn trong 30 ngày tới.')).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})
