import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { queryKeys } from '@/shared/constants/query-keys'
import { useLeaveApprovalDecision } from './use-leave'

const approveInstance = vi.fn().mockResolvedValue({})

vi.mock('../api/leave-api', () => ({
  leaveApi: { approveInstance: (...args: unknown[]) => approveInstance(...args) },
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

beforeEach(() => vi.clearAllMocks())

function setup(options?: Parameters<typeof useLeaveApprovalDecision>[0]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const invalidate = vi.spyOn(client, 'invalidateQueries')
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
  const hook = renderHook(() => useLeaveApprovalDecision(options), { wrapper })
  return { hook, invalidate }
}

describe('useLeaveApprovalDecision', () => {
  it('chỉ dọn hr + approval khi phiếu không có hệ quả ở phân hệ khác', async () => {
    const { hook, invalidate } = setup()
    act(() => hook.result.current.mutate({ instanceId: 5, decision: 'approve' }))
    await waitFor(() => expect(invalidate).toHaveBeenCalledTimes(2))
    const keys = invalidate.mock.calls.map(([filters]) => filters?.queryKey)
    expect(keys).toEqual([queryKeys.hr.all, queryKeys.approval.all])
  })

  it('duyệt chặng cuối thanh toán nghỉ phép: dọn thêm nhánh finance (YCTT mới sinh)', async () => {
    const { hook, invalidate } = setup({ alsoInvalidate: [queryKeys.finance.all] })
    act(() => hook.result.current.mutate({ instanceId: 5, decision: 'approve' }))
    await waitFor(() => expect(invalidate).toHaveBeenCalledTimes(3))
    const keys = invalidate.mock.calls.map(([filters]) => filters?.queryKey)
    expect(keys).toContainEqual(queryKeys.finance.all)
  })
})
