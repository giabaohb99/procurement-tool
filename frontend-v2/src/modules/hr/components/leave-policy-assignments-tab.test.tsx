import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LeavePolicyAssignmentsTab } from './leave-policy-assignments-tab'

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

const header = (text: string) => screen.getByText(text, { selector: 'thead span' })
const lastParams = () => {
  const calls = apiGet.mock.calls.filter(([url]) => url === '/api/leave-policy-assignments')
  return (calls.at(-1)?.[1] as { params: Record<string, unknown> }).params
}

beforeEach(() => {
  granted = new Set(['leave_balance.read'])
  apiGet.mockReset().mockResolvedValue({ total: 0, items: [] })
})

//  duoc-CR-748: tab "Đang phân bổ" của một chính sách xếp cột tại MÁY CHỦ, trạng thái xếp ở state cục bộ.
describe('LeavePolicyAssignmentsTab — sắp xếp cột (duoc-CR-748)', () => {
  function renderTab() {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    return render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <LeavePolicyAssignmentsTab policyId={4} />
        </MemoryRouter>
      </QueryClientProvider>,
    )
  }

  it('gửi khóa xếp kèm policy_id; cột Chính sách vắng ở tab này; Hạn mức năm nay không xếp được', async () => {
    const user = userEvent.setup()
    renderTab()
    await screen.findByText('Nhân sự', { selector: 'thead span' })
    expect(screen.queryByText('Chính sách', { selector: 'thead span' })).toBeNull()
    await user.click(header('Nhân sự'))
    await waitFor(() => expect(lastParams()).toMatchObject({ policy_id: 4, sort_by: 'employee_name', sort_dir: 'asc', page: 1 }))
    await user.click(header('Trạng thái'))
    await waitFor(() => expect(lastParams()).toMatchObject({ sort_by: 'state', sort_dir: 'asc' }))
    await user.click(header('Trạng thái'))
    await waitFor(() => expect(lastParams()).toMatchObject({ sort_by: 'state', sort_dir: 'desc' }))
    await user.click(header('Trạng thái'))
    await waitFor(() => expect(lastParams().sort_by).toBeUndefined())
    await user.click(header('Hạn mức năm nay'))
    expect(lastParams().sort_by).toBeUndefined()
  })
})
