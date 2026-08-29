import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { queryKeys } from '@/shared/constants/query-keys'
import { WORK_TASK_STATUS, type WorkTask } from '../types/work'

/*  Lỗi QA 29/08 mà tệp này khóa lại: tick việc con trong panel chi tiết thì ô
    tick KHÔNG nhúc nhích, dù máy chủ đã ghi xong. Nguyên nhân là nó dùng chung
    `useUpdateTask` — hàm đó vá ảnh lạc quan vào `board.tasks` (chỉ có task CHA,
    C-05) nên không khớp dòng nào, rồi làm mới khóa `task(subtaskId)` trong khi
    panel đang đọc `task(parentId)`. Đừng gộp hai hook này lại.  */

const update = vi.fn()
vi.mock('../api/work-task-api', () => ({
  workTaskApi: { update: (...args: unknown[]) => update(...args) },
}))

const { useToggleSubtask } = await import('./use-work-board')

const PARENT_ID = 7
const LIST_ID = 3

function makeTask(id: number, status: number, extra: Partial<WorkTask> = {}): WorkTask {
  return {
    id,
    list_id: LIST_ID,
    section_id: null,
    parent_id: null,
    title: `Việc ${id}`,
    description: '',
    status,
    start_date: '',
    due_date: '',
    sort_order: 0,
    creator_employee_id: 1,
    completed_at: null,
    completed_by: null,
    created_at: '2026-08-29T00:00:00',
    updated_at: '2026-08-29T00:00:00',
    assignees: [],
    labels: [],
    subtask_done: 0,
    subtask_total: 0,
    comment_count: 0,
    ...extra,
  }
}

/** Task cha có 2 việc con: #101 đã xong, #102 chưa — đúng ảnh chụp màn hình QA. */
function parentWithSubtasks(): WorkTask {
  return makeTask(PARENT_ID, WORK_TASK_STATUS.OPEN, {
    subtask_done: 1,
    subtask_total: 2,
    subtasks: [
      makeTask(101, WORK_TASK_STATUS.DONE, { parent_id: PARENT_ID }),
      makeTask(102, WORK_TASK_STATUS.OPEN, { parent_id: PARENT_ID }),
    ],
  })
}

let queryClient: QueryClient

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

function parentInCache() {
  return queryClient.getQueryData<WorkTask>(queryKeys.work.task(PARENT_ID))
}

beforeEach(() => {
  update.mockReset()
  update.mockResolvedValue(undefined)
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  queryClient.setQueryData(queryKeys.work.task(PARENT_ID), parentWithSubtasks())
})

describe('useToggleSubtask', () => {
  it('ticks the subtask in the PARENT cache entry, not the subtask key', async () => {
    const { result } = renderHook(() => useToggleSubtask(LIST_ID), { wrapper })

    await act(async () => {
      result.current.mutate({ parentId: PARENT_ID, subtaskId: 102, done: true })
    })

    const subtasks = parentInCache()?.subtasks ?? []
    expect(subtasks.find((s) => s.id === 102)?.status).toBe(WORK_TASK_STATUS.DONE)
    //  Khóa cũ `task(102)` không được đụng tới — panel không đọc nó bao giờ.
    expect(queryClient.getQueryData(queryKeys.work.task(102))).toBeUndefined()
  })

  it('recounts n/m so the progress bar moves with the checkbox', async () => {
    const { result } = renderHook(() => useToggleSubtask(LIST_ID), { wrapper })

    await act(async () => {
      result.current.mutate({ parentId: PARENT_ID, subtaskId: 102, done: true })
    })

    expect(parentInCache()?.subtask_done).toBe(2)
    expect(parentInCache()?.subtask_total).toBe(2)
  })

  it('unticks back to OPEN and drops the done count', async () => {
    const { result } = renderHook(() => useToggleSubtask(LIST_ID), { wrapper })

    await act(async () => {
      result.current.mutate({ parentId: PARENT_ID, subtaskId: 101, done: false })
    })

    const subtasks = parentInCache()?.subtasks ?? []
    expect(subtasks.find((s) => s.id === 101)?.status).toBe(WORK_TASK_STATUS.OPEN)
    expect(parentInCache()?.subtask_done).toBe(0)
  })

  it('sends the status to the SUBTASK id, never the parent id', async () => {
    const { result } = renderHook(() => useToggleSubtask(LIST_ID), { wrapper })

    await act(async () => {
      result.current.mutate({ parentId: PARENT_ID, subtaskId: 102, done: true })
    })

    expect(update).toHaveBeenCalledWith(102, { status: WORK_TASK_STATUS.DONE })
  })

  it('rolls the parent back when the server rejects', async () => {
    update.mockRejectedValue(new Error('403'))
    const { result } = renderHook(() => useToggleSubtask(LIST_ID), { wrapper })

    await act(async () => {
      result.current.mutate({ parentId: PARENT_ID, subtaskId: 102, done: true })
    })
    await waitFor(() => expect(result.current.isError).toBe(true))

    const subtasks = parentInCache()?.subtasks ?? []
    expect(subtasks.find((s) => s.id === 102)?.status).toBe(WORK_TASK_STATUS.OPEN)
    expect(parentInCache()?.subtask_done).toBe(1)
  })

  it('does not crash when the parent is not cached yet', async () => {
    queryClient.removeQueries({ queryKey: queryKeys.work.task(PARENT_ID) })
    const { result } = renderHook(() => useToggleSubtask(LIST_ID), { wrapper })

    await act(async () => {
      result.current.mutate({ parentId: PARENT_ID, subtaskId: 102, done: true })
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(update).toHaveBeenCalledWith(102, { status: WORK_TASK_STATUS.DONE })
  })

  it('leaves a parent whose subtasks were never loaded untouched', async () => {
    queryClient.setQueryData(
      queryKeys.work.task(PARENT_ID),
      makeTask(PARENT_ID, WORK_TASK_STATUS.OPEN),
    )
    const { result } = renderHook(() => useToggleSubtask(LIST_ID), { wrapper })

    await act(async () => {
      result.current.mutate({ parentId: PARENT_ID, subtaskId: 102, done: true })
    })

    expect(parentInCache()?.subtasks).toBeUndefined()
    expect(parentInCache()?.subtask_done).toBe(0)
  })
})
