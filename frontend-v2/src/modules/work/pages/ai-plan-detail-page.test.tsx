import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { AiPlanDetail, AiPlanTask } from '../types/ai-plan'
import { AiPlanDetailPage } from './ai-plan-detail-page'

const apiGet = vi.fn()
const apiPut = vi.fn()
const apiPost = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPut: (...args: unknown[]) => apiPut(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

const can = vi.fn((_entity: string, _action: string) => true)
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => can(entity, action), canAccess: () => true }),
}))

vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({
    data: { total: 2, items: [{ id: 12, code: 'NSU012', full_name: 'Nguyễn A' }, { id: 13, code: 'NSU013', full_name: 'Trần B' }] },
  }),
}))

const confirmMock = vi.fn()
vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: (...args: unknown[]) => confirmMock(...args),
}))

vi.mock('../components/work-sidebar-peek-button', () => ({ WorkSidebarPeekButton: () => null }))

function task(over: Partial<AiPlanTask> = {}): AiPlanTask {
  return {
    key: 'p1t1',
    title: 'Đặt phòng họp',
    description: '',
    assignees: [{ employee_id: 12, code: 'NSU012', name: 'Nguyễn A' }],
    start_date: '2026-10-23',
    due_date: '2026-10-24',
    priority: 'Ưu tiên',
    criteria: [],
    estimate_hours: 2,
    task_type: null,
    assignee_reason: 'Ít việc nhất phòng',
    subtasks: [],
    ...over,
  }
}

function detail(over: Partial<AiPlanDetail> = {}): AiPlanDetail {
  return {
    id: 5,
    status: 1,
    status_label: 'Chờ duyệt',
    title: 'Tiếp khách',
    deadline: '2026-10-30',
    channel_label: 'Web',
    counts: { phases: 1, tasks: 2, subtasks: 0 },
    created_at: '2026-10-22T09:00:00',
    list_id: 0,
    list_url: null,
    goal: 'Đón đoàn khách',
    plan: {
      title: 'Tiếp khách',
      description: '',
      deadline: '2026-10-30',
      phases: [{ name: 'Chuẩn bị', tasks: [task(), task({ key: 'p1t2', title: 'Đặt xe' })] }],
      assumptions: [],
      counts: { phases: 1, tasks: 2, subtasks: 0 },
    },
    plan_ai: null,
    plan_final: null,
    reject_reason: '',
    decided_at: null,
    ...over,
  }
}

function LocationProbe() {
  const location = useLocation()
  return <output aria-label="vị trí">{location.pathname}</output>
}

function build(url = '/project/ai-plans/5') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route path="/project/ai-plans/:planId" element={<AiPlanDetailPage />} />
          <Route path="*" element={null} />
        </Routes>
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function mockGet(plan: AiPlanDetail) {
  apiGet.mockImplementation((url: string) => {
    if (url.startsWith('/api/ai-plans/')) return Promise.resolve(plan)
    if (url === '/api/work/task-types') return Promise.resolve({ total: 0, items: [] })
    return Promise.reject(new Error(`chưa mock ${url}`))
  })
}

beforeEach(() => {
  apiGet.mockReset()
  apiPut.mockReset()
  apiPost.mockReset()
  confirmMock.mockReset().mockResolvedValue(true)
  can.mockImplementation(() => true)
  mockGet(detail())
})

describe('AiPlanDetailPage — sửa và lưu', () => {
  it('saves the edited plan without leaking the local row ids', async () => {
    apiPut.mockResolvedValue(detail())
    build()
    const [title] = await screen.findAllByLabelText('Tên việc')
    fireEvent.change(title, { target: { value: 'Đặt phòng họp lớn' } })
    fireEvent.click(screen.getByRole('button', { name: /Lưu bản sửa/ }))

    await waitFor(() => expect(apiPut).toHaveBeenCalledTimes(1))
    const [url, body] = apiPut.mock.calls[0] as [string, { plan: { phases: { tasks: { title: string }[] }[] } }]
    expect(url).toBe('/api/ai-plans/5')
    expect(body.plan.phases[0].tasks[0].title).toBe('Đặt phòng họp lớn')
    expect(JSON.stringify(body)).not.toContain('"uid"')
  })

  it('keeps Lưu disabled until something changed', async () => {
    build()
    await screen.findAllByLabelText('Tên việc')
    expect(screen.getByRole('button', { name: /Lưu bản sửa/ })).toBeDisabled()
  })

  it('blocks saving and approving a task with no name — the server would drop it silently', async () => {
    build()
    const [title] = await screen.findAllByLabelText('Tên việc')
    fireEvent.change(title, { target: { value: '   ' } })

    expect(screen.getByText('Việc chưa có tên')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Lưu bản sửa/ })).toBeDisabled()
    expect(screen.getByRole('button', { name: /Duyệt và tạo việc/ })).toBeDisabled()
  })

  it('lets a phase emptied of tasks through with a warning — the server drops that phase on purpose', async () => {
    build()
    await screen.findAllByLabelText('Tên việc')
    fireEvent.click(screen.getByRole('button', { name: 'Bỏ việc Đặt phòng họp' }))
    fireEvent.click(screen.getByRole('button', { name: 'Bỏ việc Đặt xe' }))

    expect(screen.getByText(/giai đoạn này bị bỏ/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Duyệt và tạo việc/ })).toBeEnabled()
  })

  it('pins a 422 problem from the server under the row it points at', async () => {
    apiPut.mockRejectedValue({
      response: {
        status: 422,
        data: {
          success: false,
          error: {
            code: 'PLAN_INVALID',
            message: 'Kế hoạch chưa hợp lệ',
            details: {
              problems: [
                { phase: 0, task: 1, subtask: null, key: 'p1t2', field: 'assignees', message: '"Đặt xe": người #99 đã nghỉ việc' },
              ],
            },
          },
        },
      },
    })
    build()
    const [title] = await screen.findAllByLabelText('Tên việc')
    fireEvent.change(title, { target: { value: 'Đặt phòng' } })
    fireEvent.click(screen.getByRole('button', { name: /Lưu bản sửa/ }))

    //  Đúng dòng thứ hai (vị trí task 1), không phải dòng đầu hay câu chung của kế hoạch.
    const row = await screen.findByRole('group', { name: 'Việc: Đặt xe' })
    expect(within(row).getByText('"Đặt xe": người #99 đã nghỉ việc')).toBeInTheDocument()
    expect(
      within(screen.getByRole('group', { name: 'Việc: Đặt phòng' })).queryByText(/người #99/),
    ).toBeNull()
  })

  it('adds a task with an empty server key', async () => {
    apiPut.mockResolvedValue(detail())
    build()
    await screen.findAllByLabelText('Tên việc')
    fireEvent.click(screen.getByRole('button', { name: /^Thêm việc$/ }))
    const titles = screen.getAllByLabelText('Tên việc')
    fireEvent.change(titles[titles.length - 1], { target: { value: 'Chuẩn bị quà' } })
    fireEvent.click(screen.getByRole('button', { name: /Lưu bản sửa/ }))

    await waitFor(() => expect(apiPut).toHaveBeenCalled())
    const body = apiPut.mock.calls[0][1] as { plan: { phases: { tasks: { key: string; title: string }[] }[] } }
    expect(body.plan.phases[0].tasks.at(-1)).toMatchObject({ key: '', title: 'Chuẩn bị quà' })
  })
})

describe('AiPlanDetailPage — duyệt và từ chối', () => {
  it('approves with the plan on screen and opens the new project', async () => {
    apiPost.mockResolvedValue({ id: 5, list_id: 77, list_url: '/project/lists/77' })
    build()
    await screen.findAllByLabelText('Tên việc')
    fireEvent.click(screen.getByRole('button', { name: /Duyệt và tạo việc/ }))

    await waitFor(() => expect(screen.getByLabelText('vị trí')).toHaveTextContent('/project/lists/77'))
    const [url, body] = apiPost.mock.calls[0] as [string, { plan: unknown }]
    expect(url).toBe('/api/ai-plans/5/approve')
    expect(body.plan).toBeDefined()
  })

  it('does nothing when the confirmation is cancelled', async () => {
    confirmMock.mockResolvedValue(false)
    build()
    await screen.findAllByLabelText('Tên việc')
    fireEvent.click(screen.getByRole('button', { name: /Duyệt và tạo việc/ }))

    await waitFor(() => expect(confirmMock).toHaveBeenCalled())
    expect(apiPost).not.toHaveBeenCalled()
  })

  it('sends ONE approve on a double click — two would build two projects', async () => {
    let finish: (value: unknown) => void = () => {}
    apiPost.mockImplementation(() => new Promise((resolve) => (finish = resolve)))
    build()
    await screen.findAllByLabelText('Tên việc')
    const approve = screen.getByRole('button', { name: /Duyệt và tạo việc/ })
    fireEvent.click(approve)
    fireEvent.click(approve)

    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    finish({ id: 5, list_id: 77, list_url: '/project/lists/77' })
    await waitFor(() => expect(screen.getByLabelText('vị trí')).toHaveTextContent('/project/lists/77'))
    expect(apiPost).toHaveBeenCalledTimes(1)
  })

  it('rejects with the typed reason', async () => {
    apiPost.mockResolvedValue(detail({ status: 3, status_label: 'Từ chối', reject_reason: 'Chưa cần' }))
    build()
    await screen.findAllByLabelText('Tên việc')
    fireEvent.click(screen.getByRole('button', { name: /^Từ chối$/ }))
    fireEvent.change(await screen.findByLabelText('Lý do từ chối'), { target: { value: 'Chưa cần' } })
    const buttons = screen.getAllByRole('button', { name: /^Từ chối$/ })
    fireEvent.click(buttons[buttons.length - 1])

    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/ai-plans/5/reject', { reason: 'Chưa cần' }))
  })
})

describe('AiPlanDetailPage — chỉ xem', () => {
  it('shows an approved plan read-only, with a link to the project it created', async () => {
    mockGet(detail({ status: 2, status_label: 'Đã duyệt', list_id: 77, list_url: '/project/lists/77' }))
    build()
    const [title] = await screen.findAllByLabelText('Tên việc')

    expect(title).toHaveAttribute('readonly')
    expect(screen.queryByRole('button', { name: /Duyệt và tạo việc/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Thêm việc/ })).toBeNull()
    expect(screen.getByRole('link', { name: /Mở dự án đã tạo/ })).toHaveAttribute('href', '/project/lists/77')
  })

  it('lets someone without work_task.create read a pending plan but not change it', async () => {
    can.mockImplementation((_entity, action) => action !== 'create')
    build()
    const [title] = await screen.findAllByLabelText('Tên việc')

    expect(title).toHaveAttribute('readonly')
    expect(screen.queryByRole('button', { name: /Duyệt và tạo việc/ })).toBeNull()
    expect(screen.getByText(/chỉ có quyền xem việc/)).toBeInTheDocument()
  })

  it('says the plan was not found for a bad id, without calling the server', async () => {
    build('/project/ai-plans/abc')

    expect(await screen.findByText(/Không tìm thấy kế hoạch này/)).toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalledWith('/api/ai-plans/NaN')
  })

  it('says the same for a plan that belongs to someone else (server 404)', async () => {
    apiGet.mockImplementation((url: string) =>
      url.startsWith('/api/ai-plans/') ? Promise.reject(new Error('404')) : Promise.resolve({ total: 0, items: [] }),
    )
    build()

    expect(await screen.findByText(/Không tìm thấy kế hoạch này/)).toBeInTheDocument()
  })
})
