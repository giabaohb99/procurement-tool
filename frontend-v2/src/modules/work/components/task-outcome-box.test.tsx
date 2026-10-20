import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { workTaskTypeApi } from '../api/task-type-api'
import type { WorkTask } from '../types/work'
import { TaskOutcomeBox } from './task-outcome-box'

vi.mock('../api/task-type-api', () => ({
  workTaskTypeApi: { listActive: vi.fn(), listAll: vi.fn(), setOutcome: vi.fn() },
}))

const confirmMock = vi.hoisted(() => vi.fn())
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: confirmMock }))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

function renderBox(patch: Partial<WorkTask> = {}, opts: { done?: boolean; canEdit?: boolean } = {}) {
  const task = { id: 5, title: 'Soạn hợp đồng', outcome: 0, ...patch } as WorkTask
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <TaskOutcomeBox task={task} listId={1} canEdit={opts.canEdit ?? true} done={opts.done ?? true} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.mocked(workTaskTypeApi.setOutcome).mockReset().mockResolvedValue({} as never)
  confirmMock.mockReset()
})

describe('TaskOutcomeBox — duoc-CR-656', () => {
  it('«Đạt» gọi API ngay, không hỏi lại', async () => {
    renderBox()
    await userEvent.click(screen.getByRole('button', { name: 'Đạt' }))
    await waitFor(() => expect(workTaskTypeApi.setOutcome).toHaveBeenCalledWith(5, 1))
    expect(confirmMock).not.toHaveBeenCalled()
  })

  it('«Phải làm lại» hỏi xác nhận; từ chối thì không gọi API', async () => {
    confirmMock.mockResolvedValueOnce(false)
    renderBox()
    await userEvent.click(screen.getByRole('button', { name: 'Phải làm lại' }))
    expect(confirmMock).toHaveBeenCalledTimes(1)
    expect(workTaskTypeApi.setOutcome).not.toHaveBeenCalled()

    confirmMock.mockResolvedValueOnce(true)
    await userEvent.click(screen.getByRole('button', { name: 'Phải làm lại' }))
    await waitFor(() => expect(workTaskTypeApi.setOutcome).toHaveBeenCalledWith(5, 2))
  })

  it('bấm đúp chỉ ra MỘT request', async () => {
    let release: (v: unknown) => void = () => {}
    vi.mocked(workTaskTypeApi.setOutcome).mockReturnValue(new Promise((r) => (release = r)) as never)
    renderBox()
    const btn = screen.getByRole('button', { name: 'Đạt' })
    await userEvent.dblClick(btn)
    expect(workTaskTypeApi.setOutcome).toHaveBeenCalledTimes(1)
    release({})
  })

  it('hiện nhãn kết quả hiện tại', () => {
    renderBox({ outcome: 1 })
    expect(screen.getAllByText('Đạt').length).toBeGreaterThan(1) // nhãn + nút
  })

  it('đang làm lại (chưa xong) thì chỉ nhãn, không nút; chỉ xem cũng không nút', () => {
    renderBox({ outcome: 2 }, { done: false })
    expect(screen.getByText('Phải làm lại')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('người chỉ xem không có nút', () => {
    renderBox({ outcome: 0 }, { canEdit: false })
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
