import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const fetchDraft = vi.fn()
const fetchById = vi.fn()

vi.mock('../api/approver-candidates-api', () => ({
  fetchApproverCandidates: (...args: unknown[]) => fetchById(...args),
  fetchDraftApproverCandidates: (...args: unknown[]) => fetchDraft(...args),
}))

import { useApproverCandidates } from './use-approver-candidates'

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

const EMPTY_SCOPE = { department: '', department_id: 0, company_id: 0, handler_dept_id: 0 }

describe('useApproverCandidates', () => {
  beforeEach(() => {
    fetchDraft.mockReset().mockResolvedValue({ items: [{ employee_id: 7 }] })
    fetchById.mockReset().mockResolvedValue({ items: [] })
  })

  //  bao-CR-780: đơn mua hàng tạo thẳng chưa có phòng ban — trước đây hook không hỏi nên ô báo
  //  "Chưa có ai duyệt được phiếu này" dù backend có người duyệt.
  it('asks the draft endpoint for a new document even without a department', async () => {
    const { result } = renderHook(
      () => useApproverCandidates('purchase-orders', 0, EMPTY_SCOPE, true),
      { wrapper },
    )
    await waitFor(() => expect(result.current.data?.items).toHaveLength(1))
    expect(fetchDraft).toHaveBeenCalledWith('purchase-orders', EMPTY_SCOPE)
    expect(fetchById).not.toHaveBeenCalled()
  })

  it('does not ask when the picker is locked', () => {
    renderHook(() => useApproverCandidates('purchase-orders', 0, EMPTY_SCOPE, false), { wrapper })
    expect(fetchDraft).not.toHaveBeenCalled()
  })
})
