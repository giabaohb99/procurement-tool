import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { EmployeePendingWorkPanel } from './employee-pending-work-panel'

/** duoc-CR-665 (V0-4): khung việc đang giữ — liệt kê, chuyển từng việc, chuyển hết. */

let granted: string[] = []
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => granted.includes(`${entity}.${action}`),
    canAny: () => true,
    canAccess: () => true,
  }),
}))

const apiGet = vi.fn()
const apiPost = vi.fn()
const apiPatch = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiPost: (...a: unknown[]) => apiPost(...a),
  apiPatch: (...a: unknown[]) => apiPatch(...a),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
  extractErrorMessage: () => 'lỗi',
  httpClient: {},
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

const WORK = {
  employee_id: 3,
  tasks: [
    {
      task_id: 11, instance_id: 1, entity: 'purchase_request', entity_id: 9, entity_code: 'PYC-9',
      entity_title: 'Mua giấy', node_name: 'Trưởng phòng', status: 2, status_label: 'Đang chờ',
      due_at: null, is_overdue: false, started_by_employee_id: 5, started_by_name: 'Người nộp',
    },
  ],
  total_tasks: 1,
  flow_steps: [
    {
      flow_id: 4, flow_code: 'L1', flow_name: 'Luồng mua hàng', entity: 'purchase_order',
      node_id: 40, node_seq: 2, node_name: 'Giám đốc', role: 'approver',
    },
  ],
  total_flow_steps: 1,
}

function routeGet(work: unknown) {
  return (url: string) => {
    if (url === '/api/employees/3/pending-work') return Promise.resolve(work)
    return Promise.resolve({ items: [{ id: 8, code: 'NV8', full_name: 'Người nhận' }], total: 1 })
  }
}

function renderPanel() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <EmployeePendingWorkPanel employeeId={3} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('EmployeePendingWorkPanel', () => {
  beforeEach(() => {
    granted = ['approval_flow.write', 'employee.read']
    apiGet.mockReset()
    apiPost.mockReset().mockResolvedValue({ count: 1 })
    apiPatch.mockReset().mockResolvedValue({})
    apiGet.mockImplementation(routeGet(WORK))
  })

  it('lists pending tasks and the flow steps naming this person', async () => {
    renderPanel()
    expect(await screen.findByText(/1 việc duyệt đang chờ người này/)).toBeInTheDocument()
    expect(screen.getByText(/PYC-9/)).toBeInTheDocument()
    expect(screen.getByText('Luồng mua hàng')).toBeInTheDocument()
  })

  it('says so when nothing is pending', async () => {
    apiGet.mockImplementation(
      routeGet({ ...WORK, tasks: [], total_tasks: 0, flow_steps: [], total_flow_steps: 0 }),
    )
    renderPanel()
    expect(await screen.findByText(/không còn việc duyệt nào đang treo/i)).toBeInTheDocument()
  })

  it('hides the transfer buttons without approval_flow.write', async () => {
    granted = ['employee.read']
    renderPanel()
    await screen.findByText(/1 việc duyệt đang chờ người này/)
    expect(screen.queryByRole('button', { name: 'Chuyển' })).not.toBeInTheDocument()
    expect(screen.getByText(/không có quyền chuyển việc duyệt/i)).toBeInTheDocument()
  })

  it('keeps transfer disabled until a recipient is chosen, then reassigns one task', async () => {
    renderPanel()
    const button = await screen.findByRole('button', { name: 'Chuyển' })
    expect(button).toBeDisabled()
    await userEvent.click(screen.getByRole('combobox'))
    await userEvent.click(await screen.findByText(/Người nhận/))
    await userEvent.click(screen.getByRole('button', { name: 'Chuyển' }))
    await waitFor(() =>
      expect(apiPatch).toHaveBeenCalledWith('/api/approvals/tasks/11/reassign', {
        to_employee_id: 8,
        reason: 'Bàn giao trước khi khóa tài khoản',
      }),
    )
  })

  it('phiếu người xem không đọc được: không hiện mã, không dẫn link, vẫn chuyển được', async () => {
    const hiddenTask = {
      ...WORK.tasks[0], entity_code: '', entity_title: '', hidden: true,
      started_by_employee_id: 0, started_by_name: '',
    }
    apiGet.mockImplementation(routeGet({ ...WORK, tasks: [hiddenTask] }))
    renderPanel()
    expect(await screen.findByText(/bạn không có quyền xem phiếu này/)).toBeTruthy()
    expect(screen.queryByText(/#9/)).toBeNull()
    expect(screen.queryByRole('link', { name: /không có quyền xem/ })).toBeNull()
    expect(screen.getByRole('button', { name: 'Chuyển' })).toBeTruthy()
  })
})
