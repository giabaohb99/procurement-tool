import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useDocumentWorkflow } from './use-documents'

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))
vi.mock('../api/document-api', () => ({
  documentApi: {
    submit: vi.fn().mockResolvedValue({}),
    approve: vi.fn().mockResolvedValue({ display_code: '01/2026/QD-DEGO' }),
    reject: vi.fn().mockResolvedValue({}),
    revoke: vi.fn().mockResolvedValue({}),
    confirmReviewed: vi.fn().mockResolvedValue({}),
  },
}))

let queryClient: QueryClient
let reloaded: unknown[][]

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

beforeEach(() => {
  queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  reloaded = []
  vi.spyOn(queryClient, 'invalidateQueries').mockImplementation((filters) => {
    reloaded.push((filters?.queryKey ?? []) as unknown[])
    return Promise.resolve()
  })
})

/** Có nạp lại họ dữ liệu bắt đầu bằng khóa này không. */
function hasReload(goc: string): boolean {
  return reloaded.some((key) => key[0] === goc)
}

describe('useDocumentWorkflow', () => {
  it('gửi duyệt xong phải nạp lại CẢ phiên duyệt, không chỉ bản ghi văn bản', async () => {
    //  LỖI ĐÃ XẢY RA (20/08/2026): chỉ nạp lại `document`. Văn bản sang «Đang
    //  duyệt» nhưng phiên duyệt còn là kết quả cũ (`null`, hỏi từ lúc còn Nháp),
    //  nên trang chi tiết tưởng chưa vào bộ máy nhiều bước và vẫn bày hai nút
    //  «Trả lại» + «Duyệt và ban hành». Bấm vào chỉ nhận lỗi 409.
    const { result } = renderHook(() => useDocumentWorkflow(7), { wrapper: wrapper })

    result.current.submit.mutate()

    await waitFor(() => expect(hasReload('document')).toBe(true))
    expect(hasReload('approval')).toBe(true)
  })

  it('ban hành xong cũng nạp lại phiên duyệt', async () => {
    const { result } = renderHook(() => useDocumentWorkflow(7), { wrapper: wrapper })

    result.current.approve.mutate(undefined)

    await waitFor(() => expect(hasReload('approval')).toBe(true))
  })

  it('trả lại và bãi bỏ cũng vậy — mọi thao tác đổi trạng thái đều đụng phiên duyệt', async () => {
    const { result } = renderHook(() => useDocumentWorkflow(7), { wrapper: wrapper })

    result.current.reject.mutate('Sai nội dung')
    await waitFor(() => expect(hasReload('approval')).toBe(true))

    reloaded = []
    result.current.revoke.mutate('Hết hiệu lực')
    await waitFor(() => expect(hasReload('approval')).toBe(true))
  })
})
