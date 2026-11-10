import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { DOCUMENT_STATUS, type DocumentRecord } from '../types/document-record'
import { IncomingDocumentsTab } from './incoming-documents-tab'
import { OutgoingDocumentsTab } from './outgoing-documents-tab'

/**
 * duoc-CR-744 — bấm tiêu đề cột hai tab của màn Văn bản.
 * - Văn bản đi: phân trang ở server -> gửi `sort_by`/`sort_dir` (và Export đi cùng thứ tự); tìm TOÀN VĂN xếp
 *   theo độ khớp nên tiêu đề không bấm được.
 * - Văn bản đến: `/applies-to-me` trả trọn -> xếp tại chỗ theo giá trị ô đang hiện (trạng thái theo hạng vòng đời
 *   kể cả nhãn suy ra từ ngày; ô trống luôn xuống cuối ở cả hai chiều).
 */
const listCalls: Record<string, unknown>[] = []
let appliedItems: DocumentRecord[] = []
const { downloadFileMock } = vi.hoisted(() => ({ downloadFileMock: vi.fn() }))

vi.mock('@/core/api', () => ({ downloadFile: downloadFileMock }))
vi.mock('../hooks/use-documents', () => ({
  useDocuments: (params: Record<string, unknown>) => {
    listCalls.push(params)
    return { data: { total: 0, items: [] }, isLoading: false, isError: false }
  },
}))
vi.mock('../hooks/use-document-search', () => ({
  isFullTextQuery: (keyword: string) => keyword.trim().length >= 2,
  useDocumentSearch: () => ({ data: { total: 0, items: [] }, isLoading: false, isError: false }),
}))
vi.mock('../hooks/use-document-scopes', () => ({
  useDocumentsAppliedToMe: () => ({
    data: { total: appliedItems.length, items: appliedItems },
    isLoading: false,
    isError: false,
  }),
}))
vi.mock('../hooks/use-my-document-approvals', () => ({ useMyDocumentTasks: () => ({ items: [] }) }))
vi.mock('../hooks/use-document-types', () => ({ useActiveDocumentTypes: () => [] }))
vi.mock('../hooks/use-document-catalogs', () => ({ useSecurityLevelLabel: () => () => 'Thường' }))
vi.mock('../hooks/use-prefetch-document', () => ({ usePrefetchDocument: () => () => undefined }))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))
vi.mock('./folder-filter-control', () => ({ FolderFilterControl: () => null }))
vi.mock('./folder-bulk-actions', () => ({ FolderBulkActions: () => null }))
vi.mock('./document-copy-action', () => ({ DocumentCopyAction: () => null }))

function build(element: React.ReactElement, url: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>{element}</MemoryRouter>
    </QueryClientProvider>,
  )
}

const header = (text: string) => screen.getByText(text, { selector: 'thead span' })
//  Cuộc gọi của DANH SÁCH CHÍNH (có `page`); tab còn gọi thêm một lần hỏi các bản riêng của dòng đang bung.
const last = () => [...listCalls].reverse().find((call) => call.page !== undefined) ?? {}

/** Id văn bản theo thứ tự các dòng đang hiện trong thân bảng của tab Văn bản đến (đọc từ cột Số hiệu `SH-<id>`). */
function ids(): number[] {
  const rows = screen.getAllByRole('row').slice(1)
  return rows.map((row) => Number(within(row).getByText(/^SH-\d+$/).textContent?.replace('SH-', '')))
}

function doc(over: Partial<DocumentRecord> & { id: number }): DocumentRecord {
  return {
    display_code: `SH-${over.id}`,
    title: `VB ${over.id}`,
    doc_type_name: 'Quy chế',
    company_name: 'DEGO',
    department_name: 'HC',
    owner_name: 'An',
    secrecy_level: 1,
    status: DOCUMENT_STATUS.effective,
    effective_date: '2020-01-01',
    expire_date: null,
    needs_review: false,
    legacy_code: '',
    keywords: '',
    ...over,
  } as DocumentRecord
}

beforeEach(() => {
  listCalls.length = 0
  appliedItems = []
  downloadFileMock.mockReset()
})

describe('OutgoingDocumentsTab — sắp xếp cột (duoc-CR-744)', () => {
  it('sends the column key as sort_by for every sortable data column', async () => {
    const user = userEvent.setup()
    build(<OutgoingDocumentsTab />, '/document/documents')

    const cases: [string, string][] = [
      ['Số hiệu', 'display_code'],
      ['Số vào sổ', 'book_number_display'],
      ['Tên văn bản', 'title'],
      ['Loại', 'doc_type_name'],
      ['Pháp nhân ban hành', 'company_name'],
      ['Phòng chủ trì', 'department_name'],
      ['Bản', 'version_no'],
      ['Trạng thái', 'status'],
      ['Ngày hiệu lực', 'effective_date'],
      ['Mức mật', 'secrecy_level'],
      ['Tệp', 'attachment_count'],
    ]
    for (const [text, key] of cases) {
      await user.click(header(text))
      expect(last().sort_by, text).toBe(key)
    }
  })

  it('cycles asc -> desc -> off, drops both params and resets to page 1', async () => {
    const user = userEvent.setup()
    build(<OutgoingDocumentsTab />, '/document/documents')

    await user.click(header('Tên văn bản'))
    expect(last()).toMatchObject({ sort_by: 'title', sort_dir: 'asc', page: 1 })
    await user.click(header('Tên văn bản'))
    expect(last()).toMatchObject({ sort_by: 'title', sort_dir: 'desc' })
    await user.click(header('Tên văn bản'))
    expect(last().sort_by).toBeUndefined()
    expect(last().sort_dir).toBeUndefined()
  })

  it('exports in the SAME order the table is showing', async () => {
    const user = userEvent.setup()
    build(<OutgoingDocumentsTab />, '/document/documents?sort_by=effective_date&sort_dir=desc')

    await user.click(screen.getByRole('button', { name: /Export danh sách văn bản/ }))
    const url = String(downloadFileMock.mock.calls[0][0])
    expect(url).toContain('sort_by=effective_date')
    expect(url).toContain('sort_dir=desc')
  })

  it('drops the sort from the request and disables header clicks while full-text search is active', async () => {
    const user = userEvent.setup()
    build(<OutgoingDocumentsTab />, '/document/documents?q=quy+che&sort_by=title&sort_dir=asc')

    //  Tìm toàn văn xếp theo độ khớp: không gửi sort_by cho danh sách thường (đã tắt) và tiêu đề không bấm được.
    const before = listCalls.length
    await user.click(header('Tên văn bản'))
    expect(listCalls.length).toBe(before)
    expect(listCalls.every((call) => call.sort_by === undefined)).toBe(true)
    expect(header('Tên văn bản').closest('div')?.className ?? '').not.toContain('cursor-pointer')
  })
})

describe('IncomingDocumentsTab — sắp xếp tại chỗ (duoc-CR-744)', () => {
  it('sorts by title, blanks last in BOTH directions, and off restores the backend order', async () => {
    const user = userEvent.setup()
    appliedItems = [
      doc({ id: 1, title: 'Chi' }),
      doc({ id: 2, title: '' }),
      doc({ id: 3, title: 'An' }),
      doc({ id: 4, title: 'Bình' }),
    ]
    build(<IncomingDocumentsTab />, '/document/documents?tab=incoming')

    await user.click(header('Trích yếu'))
    expect(ids()).toEqual([3, 4, 1, 2])
    await user.click(header('Trích yếu'))
    expect(ids()).toEqual([1, 4, 3, 2])
    await user.click(header('Trích yếu'))
    expect(ids()).toEqual([1, 2, 3, 4])
  })

  it('sorts Trạng thái by lifecycle rank incl. labels derived from dates, not by the raw code', async () => {
    const user = userEvent.setup()
    const day = (offset: number) => {
      const date = new Date()
      date.setDate(date.getDate() + offset)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    }
    appliedItems = [
      doc({ id: 1, title: 'het-han', status: DOCUMENT_STATUS.effective, effective_date: day(-30), expire_date: day(-1) }),
      doc({ id: 2, title: 'chua-hieu-luc', status: DOCUMENT_STATUS.effective, effective_date: day(5) }),
      doc({ id: 3, title: 'dang-chay', status: DOCUMENT_STATUS.effective, effective_date: day(-5) }),
      doc({ id: 4, title: 'nhap', status: DOCUMENT_STATUS.draft, effective_date: null }),
      doc({ id: 5, title: 'tu-choi', status: DOCUMENT_STATUS.rejected, effective_date: null }),
    ]
    build(<IncomingDocumentsTab />, '/document/documents?tab=incoming')

    await user.click(header('Trạng thái'))
    //  nháp(4) < chưa hiệu lực(2) < đang chạy(3) < hết hiệu lực(1) < từ chối(5)
    expect(ids()).toEqual([4, 2, 3, 1, 5])
    await user.click(header('Trạng thái'))
    expect(ids()).toEqual([5, 1, 3, 2, 4])
  })

  it('sorts Hiệu lực từ by date with newest first on the first click and empty dates last', async () => {
    const user = userEvent.setup()
    appliedItems = [
      doc({ id: 1, title: 'cu', effective_date: '2026-01-01' }),
      doc({ id: 2, title: 'chua-co', effective_date: null }),
      doc({ id: 3, title: 'moi', effective_date: '2026-06-01' }),
    ]
    build(<IncomingDocumentsTab />, '/document/documents?tab=incoming')

    await user.click(header('Hiệu lực từ'))
    expect(ids()).toEqual([3, 1, 2])
    await user.click(header('Hiệu lực từ'))
    expect(ids()).toEqual([1, 3, 2])
  })
})
