import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { RagIndexPanel } from './rag-index-panel'
import type { RagIndexStatus, RagReindexMode } from '../types/setting'

const reindexDocs = vi.fn((mode: string) =>
  Promise.resolve({ task_id: 't1', mode: mode as RagReindexMode }),
)
const refetch = vi.fn()
let status: { data: RagIndexStatus | undefined; isPending: boolean; isFetching: boolean }

vi.mock('../api/setting-api', () => ({
  settingApi: { reindexDocs: (mode: string) => reindexDocs(mode) },
}))

vi.mock('../hooks/use-settings', () => ({
  useRagIndexStatus: () => ({ ...status, refetch }),
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

function setStatus(data: RagIndexStatus | undefined, isPending = false) {
  status = { data, isPending, isFetching: false }
}

beforeEach(() => {
  reindexDocs.mockClear()
  refetch.mockClear()
  setStatus({
    enabled: true,
    help_total: 87,
    faq_total: 11,
    help_indexed: 55,
    faq_indexed: 11,
    missing: 32,
    missing_help: 32,
    missing_faq: 0,
    orphans: 0,
  })
})

describe('RagIndexPanel', () => {
  it('nói thẳng ra kho đang thiếu bao nhiêu tài liệu, vì đó là thứ khiến người ta bấm', () => {
    render(<RagIndexPanel />)
    expect(screen.getByText(/55/)).toBeInTheDocument()
    expect(screen.getByText(/Còn 32 tài liệu chưa vào chỉ mục/)).toBeInTheDocument()
  })

  it('gửi mode=missing khi bấm nạp bù, mode=all khi bấm nạp lại toàn bộ', async () => {
    const nguoi = userEvent.setup()
    render(<RagIndexPanel />)
    await nguoi.click(screen.getByRole('button', { name: /Nạp bù bài thiếu/ }))
    expect(reindexDocs).toHaveBeenCalledWith('missing')
    await nguoi.click(screen.getByRole('button', { name: /Nạp lại toàn bộ/ }))
    expect(reindexDocs).toHaveBeenLastCalledWith('all')
  })

  //  RAG tắt thì backend KHÔNG gửi các con số. Đọc thẳng `help_total` lúc đó ra `undefined`,
  //  và màn hình từng có nguy cơ hiện "0/0 bài" — đọc ra như thể kho rỗng chứ không phải
  //  tính năng đang tắt. Hai chuyện đó dẫn tới hai hành động khác hẳn nhau.
  it('RAG tắt thì nói là đang tắt, không bịa ra con số', () => {
    setStatus({ enabled: false })
    render(<RagIndexPanel />)
    expect(screen.getByText(/đang tắt/)).toBeInTheDocument()
    expect(screen.queryByText(/Kho tìm kiếm đang có/)).not.toBeInTheDocument()
  })

  it('không thiếu gì thì vẫn cho bấm — số liệu là bản chụp, có thể vừa seed thêm bài', () => {
    setStatus({ enabled: true, help_total: 87, faq_total: 11, help_indexed: 87, faq_indexed: 11, missing: 0 })
    render(<RagIndexPanel />)
    expect(screen.getByText('Không thiếu tài liệu nào.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Nạp bù bài thiếu/ })).toBeEnabled()
  })

  it('còn tài liệu mồ côi thì nói rõ nạp lại toàn bộ không dọn được chúng', () => {
    setStatus({ enabled: true, help_total: 87, faq_total: 11, help_indexed: 87, faq_indexed: 11, missing: 0, orphans: 3 })
    render(<RagIndexPanel />)
    expect(screen.getByText(/3 tài liệu đã bị xóa/)).toBeInTheDocument()
  })

  it('đang đọc kho thì chưa khẳng định gì về số lượng', () => {
    setStatus(undefined, true)
    render(<RagIndexPanel />)
    expect(screen.getByText('Đang đọc kho tìm kiếm...')).toBeInTheDocument()
  })
})
