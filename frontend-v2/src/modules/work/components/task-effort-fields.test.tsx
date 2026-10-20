import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { workTaskTypeApi } from '../api/task-type-api'
import type { WorkTask } from '../types/work'
import { formatHours, parseHours } from '../utils/effort-hours'
import { TaskEffortFields } from './task-effort-fields'

vi.mock('../api/task-type-api', () => ({
  workTaskTypeApi: { listActive: vi.fn(), listAll: vi.fn(), setOutcome: vi.fn() },
}))

function makeTask(patch: Partial<WorkTask> = {}): WorkTask {
  return {
    id: 7,
    task_type_id: 0,
    task_type_name: '',
    estimate_hours: null,
    actual_hours: null,
    outcome: 0,
    ...patch,
  } as WorkTask
}

function renderFields(task: WorkTask, opts: { done?: boolean; canEdit?: boolean } = {}) {
  const onSave = vi.fn()
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <TaskEffortFields task={task} done={opts.done ?? false} canEdit={opts.canEdit ?? true} onSave={onSave} />
    </QueryClientProvider>,
  )
  return onSave
}

beforeEach(() => {
  vi.mocked(workTaskTypeApi.listActive).mockResolvedValue({
    total: 1,
    items: [{ id: 3, name: 'Báo giá NCC' }],
  } as never)
})

describe('parseHours / formatHours — duoc-CR-656', () => {
  it('đọc giờ hợp lệ, chấp nhận dấu phẩy, rỗng là xóa', () => {
    expect(parseHours('4.5')).toBe('4.5')
    expect(parseHours('4,25')).toBe('4.25')
    expect(parseHours('')).toBe('0')
    expect(parseHours('  ')).toBe('0')
  })

  it('từ chối chữ, âm, quá 999, quá 2 số lẻ', () => {
    for (const bad of ['abc', '-1', '1000', '1.234', '12.', '1e3']) expect(parseHours(bad)).toBeNull()
    expect(parseHours('999')).toBe('999')
  })

  it('đưa chuỗi máy chủ về dạng gọn', () => {
    expect(formatHours('4.50')).toBe('4.5')
    expect(formatHours('6.00')).toBe('6')
    expect(formatHours(null)).toBe('')
  })
})

describe('TaskEffortFields — duoc-CR-656', () => {
  it('lưu giờ ước lượng khi rời ô, không lưu nếu không đổi', async () => {
    const onSave = renderFields(makeTask({ estimate_hours: '4.00' }))
    const input = screen.getByRole('textbox', { name: 'Ước lượng (giờ)' })
    expect(input).toHaveValue('4')

    await userEvent.click(input)
    await userEvent.tab()
    expect(onSave).not.toHaveBeenCalled()

    await userEvent.clear(input)
    await userEvent.type(input, '6,5')
    await userEvent.tab()
    expect(onSave).toHaveBeenCalledWith({ estimate_hours: '6.5' })
  })

  it('gõ sai thì trả về giá trị cũ, không gửi gì', async () => {
    const onSave = renderFields(makeTask({ estimate_hours: '4.00' }))
    const input = screen.getByRole('textbox', { name: 'Ước lượng (giờ)' })
    await userEvent.clear(input)
    await userEvent.type(input, '1500')
    await userEvent.tab()
    expect(onSave).not.toHaveBeenCalled()
    expect(input).toHaveValue('4')
  })

  it('xóa trắng ô là gửi 0 (xóa giờ)', async () => {
    const onSave = renderFields(makeTask({ estimate_hours: '4.00' }))
    await userEvent.clear(screen.getByRole('textbox', { name: 'Ước lượng (giờ)' }))
    await userEvent.tab()
    expect(onSave).toHaveBeenCalledWith({ estimate_hours: '0' })
  })

  it('chưa xong thì không có ô giờ thực tế; xong rồi mới nhập được và có nhắc nhẹ', async () => {
    const { unmount } = renderLocal(makeTask(), false)
    expect(screen.queryByRole('textbox', { name: 'Thực tế (giờ)' })).not.toBeInTheDocument()
    expect(screen.getByText(/Nhập được khi công việc đã hoàn thành/)).toBeInTheDocument()
    unmount()

    const onSave = renderFields(makeTask(), { done: true })
    const input = screen.getByRole('textbox', { name: 'Thực tế (giờ)' })
    expect(input).toHaveAttribute('placeholder', 'Nhập nếu nhớ — không bắt buộc')
    await userEvent.type(input, '6')
    await userEvent.tab()
    expect(onSave).toHaveBeenCalledWith({ actual_hours: '6' })
  })

  it('chỉ xem thì hiện chữ, không có ô nhập', () => {
    renderFields(makeTask({ estimate_hours: '4.00' }), { canEdit: false })
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.getByText('4 giờ')).toBeInTheDocument()
  })

  it('loại việc đã ngừng dùng của việc cũ vẫn hiện tên đang gán', async () => {
    renderFields(makeTask({ task_type_id: 99, task_type_name: 'Loại cũ' }))
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Loại việc' })).toHaveTextContent('Loại cũ'))
  })
})

function renderLocal(task: WorkTask, done: boolean) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <TaskEffortFields task={task} done={done} canEdit onSave={vi.fn()} />
    </QueryClientProvider>,
  )
}
