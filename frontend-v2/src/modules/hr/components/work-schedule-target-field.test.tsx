import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { useForm, useWatch, type Control } from 'react-hook-form'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { CrudRecord } from '@/shared/crud'
import { WorkScheduleLevelField } from './work-schedule-level-field'
import { WorkScheduleTargetField } from './work-schedule-target-field'

const apiGet = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

function Probe({ control }: { control: Control<CrudRecord> }) {
  const level = useWatch({ control, name: 'target_level' })
  const id = useWatch({ control, name: 'target_id' })
  return <output data-testid="probe">{JSON.stringify({ level, id })}</output>
}

function Harness({
  level,
  id,
  savedName = '',
  onValid,
}: {
  level: number
  id: number
  savedName?: string
  onValid?: () => void
}) {
  const { control, handleSubmit } = useForm<CrudRecord>({
    defaultValues: { target_level: level, target_id: id, target_name: savedName },
  })
  //  Một client cho cả vòng đời — dựng mới mỗi lần vẽ thì cache mất và truy vấn chạy lại liên tục.
  const [client] = useState(() => new QueryClient({ defaultOptions: { queries: { retry: false } } }))
  return (
    <QueryClientProvider client={client}>
      <form onSubmit={handleSubmit(() => onValid?.())}>
        <button type="submit">Lưu thử</button>
        <WorkScheduleLevelField control={control} name="target_level" idName="target_id" />
        <WorkScheduleTargetField control={control} name="target_id" levelName="target_level" />
        <Probe control={control} />
      </form>
    </QueryClientProvider>
  )
}

const probe = () => JSON.parse(screen.getByTestId('probe').textContent ?? '{}') as { level: number; id: number }

describe('WorkScheduleLevelField + WorkScheduleTargetField', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiGet.mockImplementation(async (url: string) => {
      if (url === '/api/employees') return { items: [{ id: 12, code: 'NV012', full_name: 'Lê Văn A' }] }
      if (url === '/api/companies') return { items: [{ id: 12, name: 'DEGO Holding' }] }
      return { items: [] }
    })
  })

  it('changing the level EMPLOYEE -> COMPANY clears the old target id (no wrong-target assignment)', async () => {
    const user = userEvent.setup()
    render(<Harness level={4} id={12} />)
    expect(probe()).toEqual({ level: 4, id: 12 })

    await user.click(screen.getByRole('combobox', { name: /Cấp áp dụng/ }))
    await user.click(await screen.findByRole('option', { name: 'Pháp nhân' }))

    expect(probe()).toEqual({ level: 2, id: 0 })
  })

  it('level SYSTEM shows no picker, just «Toàn hệ thống», and target id stays 0', async () => {
    const user = userEvent.setup()
    render(<Harness level={4} id={12} />)

    await user.click(screen.getByRole('combobox', { name: /Cấp áp dụng/ }))
    await user.click(await screen.findByRole('option', { name: 'Toàn hệ thống' }))

    //  Một ở ô chọn cấp, một ở ô chỉ xem của đối tượng — đúng MỘT nhãn cho cấp này, không còn «Toàn công ty».
    expect(screen.getAllByText('Toàn hệ thống').length).toBeGreaterThanOrEqual(2)
    expect(screen.queryByText('Toàn công ty')).not.toBeInTheDocument()
    expect(probe().id).toBe(0)
    expect(apiGet).not.toHaveBeenCalledWith('/api/companies', expect.anything())
  })

  it('loading an existing record does NOT wipe its target (editing keeps the stored id)', async () => {
    render(<Harness level={3} id={7} />)
    await waitFor(() => expect(apiGet).toHaveBeenCalledWith('/api/departments', expect.anything()))
    expect(probe()).toEqual({ level: 3, id: 7 })
  })

  it('an empty source list renders the empty state instead of crashing, and keeps the stored id visible', async () => {
    render(<Harness level={3} id={7} />)
    await waitFor(() => expect(apiGet).toHaveBeenCalled())
    expect(await screen.findByDisplayValue('#7')).toBeInTheDocument()
  })

  // Regression: đối tượng đã lưu mà không còn trong danh sách từng hiện «#7» vô nghĩa.
  it('shows the saved target_name instead of #id when the target is no longer in the list', async () => {
    render(<Harness level={3} id={7} savedName="Phòng Kế toán" />)
    await waitFor(() => expect(apiGet).toHaveBeenCalled())
    expect(await screen.findByDisplayValue('Phòng Kế toán')).toBeInTheDocument()
    expect(screen.queryByDisplayValue('#7')).not.toBeInTheDocument()
  })

  it('submitting with no level shows a Vietnamese message and does not submit', async () => {
    const user = userEvent.setup()
    const onValid = vi.fn()
    render(<Harness level={0} id={0} onValid={onValid} />)
    await user.click(screen.getByRole('button', { name: 'Lưu thử' }))
    expect(await screen.findByText('Chọn cấp áp dụng.')).toBeInTheDocument()
    expect(onValid).not.toHaveBeenCalled()
  })

  it('a non-SYSTEM level without a target is blocked with a message; SYSTEM with id 0 passes', async () => {
    const user = userEvent.setup()
    const onValid = vi.fn()
    const { unmount } = render(<Harness level={3} id={0} onValid={onValid} />)
    await user.click(screen.getByRole('button', { name: 'Lưu thử' }))
    expect(await screen.findByText('Chọn đối tượng áp dụng.')).toBeInTheDocument()
    expect(onValid).not.toHaveBeenCalled()
    unmount()

    render(<Harness level={1} id={0} onValid={onValid} />)
    await user.click(screen.getByRole('button', { name: 'Lưu thử' }))
    await waitFor(() => expect(onValid).toHaveBeenCalledTimes(1))
  })

  it('a failing source shows a short error and no crash', async () => {
    apiGet.mockRejectedValue(new Error('boom'))
    render(<Harness level={2} id={0} />)
    expect(await screen.findByText(/Không tải được danh sách đối tượng/)).toBeInTheDocument()
  })

  it('tolerates a source that returns a bare array, null or garbage', async () => {
    for (const payload of [[{ id: 1, name: 'Công ty A' }], null, 'x', {}]) {
      apiGet.mockResolvedValue(payload)
      const { unmount } = render(<Harness level={2} id={0} />)
      await waitFor(() => expect(apiGet).toHaveBeenCalled())
      expect(screen.getByRole('combobox', { name: /Cấp áp dụng/ })).toBeInTheDocument()
      unmount()
    }
  })

  it('no level chosen yet renders no target picker at all', () => {
    render(<Harness level={0} id={0} />)
    expect(screen.queryByText('Đối tượng áp dụng')).not.toBeInTheDocument()
    expect(apiGet).not.toHaveBeenCalled()
  })
})
