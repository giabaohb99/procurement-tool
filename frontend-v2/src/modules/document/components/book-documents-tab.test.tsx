import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import * as ReactRouterDom from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { BookDocumentsTab } from './book-documents-tab'
import { useDocuments } from '../hooks/use-documents'
import { DOCUMENT_STATUS, type DocumentRecord } from '../types/document-record'

/**
 * `DataTable` tự gọi `useQueryClient()` (nút «Tải lại») VÀ `useSearchParams()`
 * (nút «Xóa lọc», qua `FilterResetButton`), nên cần cả `QueryClientProvider`
 * thật lẫn `MemoryRouter` thật — mock trần `react-router-dom` chỉ còn
 * `useNavigate` thì hai chỗ kia chết ngay ở bước dựng cây.
 */
function renderTab(props: Parameters<typeof BookDocumentsTab>[0]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <ReactRouterDom.MemoryRouter>
        <BookDocumentsTab {...props} />
      </ReactRouterDom.MemoryRouter>
    </QueryClientProvider>,
  )
}

const navigate = vi.fn()
//  Mặc định CÓ quyền — chỉ ca kiểm "không mount" mới tắt.
let canReadDocument = true

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof ReactRouterDom>()
  return { ...actual, useNavigate: () => navigate }
})

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: PermissionEntity, action: PermissionAction) =>
      entity === 'document' && action === 'read' ? canReadDocument : true,
  }),
}))

vi.mock('../hooks/use-documents', () => ({ useDocuments: vi.fn() }))

function row(overrides: Partial<DocumentRecord> = {}): DocumentRecord {
  return {
    id: 501,
    origin: 1,
    doc_code: null,
    issue_number: '01/2026/TB-DEGO',
    display_code: '01/2026/TB-DEGO',
    seq_no: 1,
    issue_year: 2026,
    allow_manual_number: false,
    legacy_code: '',
    storage_location: '',
    metadata: null,
    doc_type_id: 1,
    doc_type_name: 'Thông báo',
    doc_type_code: 'TB',
    company_id: 1,
    company_name: 'DEGO',
    department_id: 1,
    department_name: 'Hành chính',
    owner_employee_id: 1,
    owner_name: 'Người phụ trách',
    drafter_employee_id: 2,
    drafter_name: 'Người soạn A',
    signer_employee_id: 3,
    signer_name: 'Người ký',
    title: 'Thông báo lịch trực',
    summary: '',
    keywords: '',
    secrecy_level: 1,
    urgency: 1,
    status: DOCUMENT_STATUS.effective,
    status_label: 'Có hiệu lực',
    effective_date: '2026-01-01',
    expire_date: null,
    attachment_view_until: null,
    attachment_view_window_enabled: true,
    has_content: true,
    book_id: 9,
    book_name: 'Sổ Thông báo',
    book_seq_no: 3,
    book_year: 2026,
    book_number_display: 'TB 03/2026',
    current_version_id: 1,
    version_no: '1.0',
    version_count: 1,
    attachment_count: 0,
    needs_review: false,
    needs_review_note: '',
    apply_mode: 1,
    content_mode: 1,
    created_at: '2026-01-01T00:00:00',
    ...overrides,
  }
}

function mockDocuments(items: DocumentRecord[]) {
  vi.mocked(useDocuments).mockReturnValue({
    data: { items, total: items.length },
    isLoading: false,
    isError: false,
  } as unknown as ReturnType<typeof useDocuments>)
}

beforeEach(() => {
  navigate.mockReset()
  canReadDocument = true
  mockDocuments([row()])
})

describe('BookDocumentsTab', () => {
  it('không có document.read thì KHÔNG mount bảng — không gọi useDocuments, hiện câu giải thích', () => {
    canReadDocument = false
    renderTab({ bookId: 9, year: 2026, onYearChange: vi.fn() })

    expect(
      screen.getByText(/không xem được danh sách văn bản trong sổ này/),
    ).toBeVisible()
    //  Chốt quan trọng nhất của bài này: KHÔNG được để lọt một request 403 âm
    //  thầm — thành viên sổ thiếu `document.read` không nên thấy toast lỗi.
    expect(useDocuments).not.toHaveBeenCalled()
  })

  it('có quyền thì hỏi đúng sổ, đúng năm, mặc định sắp theo số vào sổ giảm dần', () => {
    renderTab({ bookId: 9, year: 2026, onYearChange: vi.fn() })

    expect(useDocuments).toHaveBeenCalledWith(
      expect.objectContaining({
        book_id: 9,
        book_year: 2026,
        sort: '-book_seq_no',
        page: 1,
      }),
    )
  })

  it('vẽ đủ Số trong sổ · Loại · Người soạn · badge Trạng thái của mỗi dòng', () => {
    renderTab({ bookId: 9, year: 2026, onYearChange: vi.fn() })

    expect(screen.getByText('3')).toBeVisible()
    expect(screen.getByText('Thông báo')).toBeVisible()
    expect(screen.getByText('Người soạn A')).toBeVisible()
    //  Badge dùng chung `effectiveStatusBadge` — cùng nhãn với bảng Văn bản đi.
    expect(screen.getByText('Có hiệu lực')).toBeVisible()
  })

  it('văn bản chưa vào sổ hiện gạch ngang ở cột Số trong sổ, không phải ô trống hay "0"', () => {
    mockDocuments([row({ book_seq_no: null })])
    renderTab({ bookId: 9, year: 2026, onYearChange: vi.fn() })

    expect(screen.getByText('—')).toBeVisible()
    expect(screen.queryByText('0')).not.toBeInTheDocument()
  })

  it('chưa cấp số hiện chữ "Chưa cấp số" thay vì ô trống', () => {
    mockDocuments([row({ display_code: '' })])
    renderTab({ bookId: 9, year: 2026, onYearChange: vi.fn() })

    expect(screen.getByText('Chưa cấp số')).toBeVisible()
  })

  it('bấm dòng đi thẳng vào chi tiết văn bản', async () => {
    const user = userEvent.setup()
    renderTab({ bookId: 9, year: 2026, onYearChange: vi.fn() })

    await user.click(screen.getByText('Thông báo lịch trực'))
    expect(navigate).toHaveBeenCalledWith('/document/documents/501')
  })

  it('nút «Mở ở màn Văn bản» dẫn sang danh sách lọc theo book_id__eq của đúng sổ', async () => {
    const user = userEvent.setup()
    renderTab({ bookId: 9, year: 2026, onYearChange: vi.fn() })

    await user.click(screen.getByRole('button', { name: 'Mở ở màn Văn bản' }))
    expect(navigate).toHaveBeenCalledWith('/document/documents?book_id__eq=9')
  })

  it('rỗng vì SỔ CHƯA CÓ VĂN BẢN nói rõ năm đang xem', () => {
    mockDocuments([])
    renderTab({ bookId: 9, year: 2026, onYearChange: vi.fn() })

    expect(screen.getByText('Sổ chưa có văn bản nào trong năm 2026.')).toBeVisible()
  })

  /**
   * ⚠️ Bài quan trọng: gộp một câu rỗng cho cả hai ca thì người gõ nhầm một
   * chữ đọc ra "sổ chưa dùng bao giờ" — sai sự thật, và dễ khiến họ đi báo lỗi
   * nhầm chỗ thay vì sửa lại từ khóa.
   */
  it('rỗng vì TỪ KHÓA nói khác hẳn câu "sổ chưa có văn bản"', async () => {
    mockDocuments([])
    const user = userEvent.setup()
    renderTab({ bookId: 9, year: 2026, onYearChange: vi.fn() })

    await user.type(screen.getByPlaceholderText(/Tìm tên, số hiệu/), 'abc')

    await waitFor(() => {
      expect(
        screen.getByText('Không tìm thấy văn bản nào khớp từ khóa đang tìm.'),
      ).toBeVisible()
    })
    expect(screen.queryByText(/Sổ chưa có văn bản nào/)).not.toBeInTheDocument()
  })
})
