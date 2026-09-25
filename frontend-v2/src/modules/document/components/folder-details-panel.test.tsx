import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { FolderDetailsPanel } from './folder-details-panel'
import { DOCUMENT_STATUS, type DocumentRecord } from '../types/document-record'
import { FOLDER_ACCESS_LEVEL, type DocFolderDetail } from '../types/document-folder'

//  `FolderDetailsPanel` tra `display_name` qua `useFolderDisplayNameLookup`
//  (chốt dọn gọn lead 24/09/2026 tối) — hàm đó gọi `useDocFolderTree`, cần
//  giả lập để khỏi đòi `QueryClientProvider` thật cho một bài kiểm không liên
//  quan gì tới việc tra cứu đó (không có thư mục nào trong `rows` → hàm tự
//  RƠI VỀ đúng tên đã truyền, xem `use-folder-display-name-lookup.ts`).
vi.mock('../hooks/use-document-folders', () => ({ useDocFolderTree: vi.fn(() => ({ data: undefined })) }))

function folder(overrides: Partial<DocFolderDetail> = {}): DocFolderDetail {
  return {
    id: 5,
    company_id: 1,
    parent_id: 1,
    kind: 2,
    kind_label: 'Thư mục',
    name: 'Hợp đồng',
    code: '',
    path: '/1/5/',
    depth: 2,
    sort_order: 0,
    status: 1,
    status_label: 'Đang dùng',
    document_count: 3,
    document_count_branch: 7,
    my_level: FOLDER_ACCESS_LEVEL.view,
    description: '',
    breadcrumb: [{ id: 1, name: 'CÔNG TY A' }],
    effective_access: [],
    ...overrides,
  }
}

function doc(overrides: Partial<DocumentRecord> = {}): DocumentRecord {
  return {
    id: 9,
    origin: 1,
    doc_code: null,
    issue_number: '',
    display_code: 'DEGO-QC-009',
    seq_no: 9,
    issue_year: 2026,
    allow_manual_number: false,
    legacy_code: '',
    storage_location: '',
    metadata: null,
    doc_type_id: 3,
    doc_type_name: 'Quy chế / Quy trình',
    doc_type_code: 'QC',
    company_id: 1,
    company_name: 'CÔNG TY A',
    department_id: 2,
    department_name: 'Phòng Kế toán',
    owner_employee_id: 1,
    owner_name: 'Dego Admin',
    drafter_employee_id: 1,
    drafter_name: 'Người soạn X',
    signer_employee_id: 0,
    signer_name: '',
    title: 'Quy chế thử',
    summary: '',
    keywords: '',
    secrecy_level: 2,
    urgency: 1,
    status: DOCUMENT_STATUS.draft,
    status_label: 'Nháp',
    effective_date: null,
    expire_date: null,
    attachment_view_until: null,
    attachment_view_window_enabled: true,
    has_content: true,
    book_id: null,
    book_name: '',
    book_seq_no: null,
    book_year: null,
    book_number_display: '',
    current_version_id: null,
    version_no: '1.0',
    version_count: 1,
    attachment_count: 0,
    needs_review: false,
    needs_review_note: '',
    apply_mode: 1,
    content_mode: 1,
    created_at: '2026-09-01T08:00:00',
    folders: [{ id: 5, name: 'Hợp đồng', is_primary: true }],
    ...overrides,
  }
}

describe('FolderDetailsPanel', () => {
  it('kind=none: câu gợi ý chọn một mục, không có nội dung chi tiết nào', () => {
    render(<FolderDetailsPanel item={{ kind: 'none' }} onClose={vi.fn()} />)
    expect(screen.getByText(/Chọn một thư mục hoặc văn bản/)).toBeInTheDocument()
  })

  it('kind=multiple: hiện đúng số lượng đã chọn', () => {
    render(<FolderDetailsPanel item={{ kind: 'multiple', count: 4 }} onClose={vi.fn()} />)
    expect(screen.getByText('Đã chọn 4 mục.')).toBeInTheDocument()
  })

  it('kind=folder mức Xem: hiện tên, đường dẫn, số văn bản, mức quyền — KHÔNG hiện khối «Ai có quyền»', () => {
    render(
      <FolderDetailsPanel
        item={{ kind: 'folder', folder: folder({ my_level: FOLDER_ACCESS_LEVEL.view }) }}
        onClose={vi.fn()}
      />,
    )
    expect(screen.getByText('Hợp đồng')).toBeInTheDocument()
    expect(screen.getByText('CÔNG TY A')).toBeInTheDocument()
    expect(screen.getByText('7')).toBeInTheDocument()
    expect(screen.getByText('Xem')).toBeInTheDocument()
    expect(screen.queryByText('Ai có quyền')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Quản lý quyền' })).not.toBeInTheDocument()
  })

  it('kind=folder mức Quản lý: hiện khối «Ai có quyền» kèm số dòng ĐANG HIỆU LỰC', () => {
    render(
      <FolderDetailsPanel
        item={{
          kind: 'folder',
          folder: folder({
            my_level: FOLDER_ACCESS_LEVEL.manage,
            effective_access: [
              { id: 1, folder_id: 5, folder_name: 'Hợp đồng', is_inherited: false, subject_kind: 1,
                subject_kind_label: 'Người', subject_id: 1, subject_name: 'A', effect: 1,
                effect_label: 'Cho phép', level: 1, level_label: 'Xem', valid_from: null,
                valid_to: null, reason: '', is_active: true, revoked_at: '' },
              { id: 2, folder_id: 5, folder_name: 'Hợp đồng', is_inherited: false, subject_kind: 1,
                subject_kind_label: 'Người', subject_id: 2, subject_name: 'B', effect: 1,
                effect_label: 'Cho phép', level: 1, level_label: 'Xem', valid_from: null,
                valid_to: null, reason: '', is_active: false, revoked_at: '2026-01-01' },
            ],
          }),
        }}
        onClose={vi.fn()}
      />,
    )
    expect(screen.getByText('Ai có quyền')).toBeInTheDocument()
    //  Chỉ đếm dòng CÒN HIỆU LỰC (is_active) — dòng đã thu hồi không tính.
    expect(screen.getByText(/1 người\/nhóm đang có quyền/)).toBeInTheDocument()
  })

  it('kind=folder mức Quản lý: bấm «Quản lý quyền» gọi đúng callback', async () => {
    const user = userEvent.setup()
    const onManage = vi.fn()
    render(
      <FolderDetailsPanel
        item={{ kind: 'folder', folder: folder({ my_level: FOLDER_ACCESS_LEVEL.manage }) }}
        onClose={vi.fn()}
        onManagePermissions={onManage}
      />,
    )
    await user.click(screen.getByRole('button', { name: /Quản lý quyền/ }))
    expect(onManage).toHaveBeenCalledOnce()
  })

  it('kind=document: hiện số hiệu, loại, trạng thái, người soạn, thư mục chứa (đánh dấu «Chính»)', () => {
    render(<FolderDetailsPanel item={{ kind: 'document', document: doc() }} onClose={vi.fn()} />)
    expect(screen.getByText('DEGO-QC-009')).toBeInTheDocument()
    expect(screen.getByText('Quy chế / Quy trình')).toBeInTheDocument()
    expect(screen.getByText('Người soạn X')).toBeInTheDocument()
    expect(screen.getByText('Chính')).toBeInTheDocument()
  })

  it('kind=document không nằm trong thư mục nào (folders rỗng) — câu rõ ràng, không phải danh sách trống trơn', () => {
    render(<FolderDetailsPanel item={{ kind: 'document', document: doc({ folders: [] }) }} onClose={vi.fn()} />)
    expect(screen.getByText(/Không thấy thư mục nào chứa văn bản này/)).toBeInTheDocument()
  })

  it('kind=document: bấm «Mở» gọi đúng callback', async () => {
    const user = userEvent.setup()
    const onOpen = vi.fn()
    render(<FolderDetailsPanel item={{ kind: 'document', document: doc() }} onClose={vi.fn()} onOpenDocument={onOpen} />)
    await user.click(screen.getByRole('button', { name: 'Mở' }))
    expect(onOpen).toHaveBeenCalledOnce()
  })

  it('bấm nút đóng gọi onClose', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    render(<FolderDetailsPanel item={{ kind: 'none' }} onClose={onClose} />)
    await user.click(screen.getByRole('button', { name: 'Đóng khung chi tiết' }))
    expect(onClose).toHaveBeenCalledOnce()
  })
})
