import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { FolderListView } from './folder-list-view'
import { folderItemKey } from '../helpers/folder-item-id'
import { useItemSelection } from '../hooks/use-item-selection'
import {
  useCreateDocFolder,
  useDeleteDocFolder,
  useDocFolderTree,
  useUpdateDocFolder,
} from '../hooks/use-document-folders'
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND, FOLDER_STATUS } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'
import type { DocumentRecord } from '../types/document-record'

vi.mock('sonner', () => ({ toast: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }))
vi.mock('../hooks/use-document-folders', () => ({
  useDocFolderTree: vi.fn(() => ({ data: undefined })),
  useCreateDocFolder: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  useUpdateDocFolder: vi.fn(() => ({ mutate: vi.fn() })),
  useDeleteDocFolder: vi.fn(() => ({ mutate: vi.fn() })),
}))

const FOLDER: DocFolderTreeNode = {
  id: 5,
  company_id: 1,
  parent_id: 2,
  kind: FOLDER_KIND.normal,
  kind_label: 'Thư mục',
  name: 'Phụ lục',
  code: '',
  path: '/1/2/5/',
  depth: 2,
  sort_order: 0,
  status: FOLDER_STATUS.active,
  status_label: 'Đang dùng',
  document_count: 0,
  document_count_branch: 0,
  my_level: FOLDER_ACCESS_LEVEL.manage,
}

function document(
  overrides: Partial<DocumentRecord> & { id: number; title: string },
): DocumentRecord {
  return {
    origin: 1,
    doc_code: null,
    issue_number: '',
    display_code: `DEGO-${overrides.id}`,
    seq_no: null,
    issue_year: null,
    allow_manual_number: false,
    legacy_code: '',
    storage_location: '',
    metadata: null,
    doc_type_id: 1,
    doc_type_name: 'Thông báo',
    doc_type_code: 'TB',
    company_id: 1,
    company_name: 'CÔNG TY',
    department_id: null,
    department_name: '',
    owner_employee_id: 1,
    owner_name: 'Nguyễn Văn A',
    drafter_employee_id: 1,
    drafter_name: 'Nguyễn Văn A',
    signer_employee_id: null,
    signer_name: '',
    summary: '',
    keywords: '',
    secrecy_level: 2,
    urgency: 1,
    status: 1,
    status_label: 'Nháp',
    effective_date: null,
    expire_date: null,
    attachment_view_until: null,
    attachment_view_window_enabled: false,
    book_id: null,
    book_name: '',
    book_seq_no: null,
    book_year: null,
    book_number_display: '',
    current_version_id: null,
    version_no: '1.0',
    version_count: 1,
    attachment_count: 0,
    has_content: true,
    needs_review: false,
    needs_review_note: '',
    apply_mode: 1,
    content_mode: 1,
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

const DOC_A = document({ id: 10, title: 'Thông báo A' })
const DOC_B = document({ id: 11, title: 'Thông báo B' })

/** Bọc `useItemSelection` thật (không giả) — bài kiểm cần hành vi chọn THẬT (bấm/Ctrl/Shift). */
function Harness(props: {
  children: DocFolderTreeNode[]
  documents: DocumentRecord[]
  onOpenFolder?: (id: number) => void
  onOpenDocument?: (document: DocumentRecord) => void
}) {
  const selection = useItemSelection([
    ...props.children.map((c) => folderItemKey('folder', c.id)),
    ...props.documents.map((d) => folderItemKey('document', d.id)),
  ])
  return (
    <FolderListView
      children={props.children}
      documents={props.documents}
      sourceFolderId={2}
      isFullText={false}
      sortField="name"
      sortDir="asc"
      onSortFieldChange={vi.fn()}
      onToggleSortDir={vi.fn()}
      selection={selection}
      onOpenFolder={props.onOpenFolder ?? vi.fn()}
      onOpenDocument={props.onOpenDocument ?? vi.fn()}
      onViewFolderDetails={vi.fn()}
      onViewDocumentDetails={vi.fn()}
      onDropOnFolder={vi.fn()}
      onMoveDocumentTo={vi.fn()}
      onRemoveDocument={vi.fn()}
      canWrite
      canDelete
    />
  )
}

beforeEach(() => {
  vi.mocked(useDocFolderTree).mockReturnValue({ data: undefined } as unknown as ReturnType<
    typeof useDocFolderTree
  >)
  vi.mocked(useCreateDocFolder).mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof useCreateDocFolder>)
  vi.mocked(useUpdateDocFolder).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<
    typeof useUpdateDocFolder
  >)
  vi.mocked(useDeleteDocFolder).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<
    typeof useDeleteDocFolder
  >)
})

describe('FolderListView — rỗng', () => {
  it('không thư mục, không văn bản → không dựng gì cả', () => {
    const { container } = render(<Harness children={[]} documents={[]} />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('FolderListView — thư mục TRƯỚC, văn bản SAU (đặc tả B, phản hồi 24/09/2026)', () => {
  it('DOM liệt kê đúng thứ tự: thư mục rồi tới từng văn bản', () => {
    render(<Harness children={[FOLDER]} documents={[DOC_A, DOC_B]} />)
    //  Khớp CHÍNH XÁC tên (không dùng regex/chuỗi con) — nút «Chia sẻ Phụ lục»
    //  của dòng thư mục cũng chứa chữ "Phụ lục" nên regex phần-chuỗi sẽ bắt
    //  nhầm cả nút đó vào danh sách.
    const rowNames = ['Phụ lục', 'Thông báo A', 'Thông báo B']
    const rows = screen.getAllByRole('button', {
      name: (accessibleName) => rowNames.includes(accessibleName),
    })
    expect(rows.map((row) => row.getAttribute('aria-label'))).toEqual(rowNames)
  })

  it('dòng thư mục hiện «—» ở các cột chỉ có nghĩa với văn bản', () => {
    render(<Harness children={[FOLDER]} documents={[]} />)
    const row = screen.getByRole('button', { name: 'Phụ lục' })
    expect(within(row).getAllByText('—').length).toBeGreaterThanOrEqual(2)
  })
})

describe('FolderListView — chọn kiểu Drive + menu chuột phải', () => {
  //  Chốt 24/09/2026: bấm MỘT LẦN là MỞ — chọn phải kèm Ctrl/⌘/Shift.
  it('plain click on a document row opens it and does NOT select it', async () => {
    const user = userEvent.setup()
    const onOpenDocument = vi.fn()
    render(<Harness children={[]} documents={[DOC_A, DOC_B]} onOpenDocument={onOpenDocument} />)
    const row = screen.getByRole('button', { name: 'Thông báo A' })
    await user.click(row)
    expect(onOpenDocument).toHaveBeenCalledTimes(1)
    expect(onOpenDocument).toHaveBeenCalledWith(DOC_A)
    expect(row).toHaveAttribute('data-selected', 'false')
  })

  //  Chốt 24/09/2026: chọn bằng Ô TICK, không bắt người dùng nhớ Shift/Ctrl.
  it('ticking a row checkbox selects it WITHOUT opening the document', async () => {
    const user = userEvent.setup()
    const onOpenDocument = vi.fn()
    render(<Harness children={[]} documents={[DOC_A, DOC_B]} onOpenDocument={onOpenDocument} />)
    await user.click(screen.getByRole('checkbox', { name: 'Chọn Thông báo A' }))
    expect(screen.getByRole('button', { name: 'Thông báo A' })).toHaveAttribute(
      'data-selected',
      'true',
    )
    expect(screen.getByRole('checkbox', { name: 'Chọn Thông báo A' })).toBeChecked()
    expect(onOpenDocument).not.toHaveBeenCalled()
  })

  it('ticking two checkboxes keeps both selected; unticking removes only that one', async () => {
    const user = userEvent.setup()
    render(<Harness children={[]} documents={[DOC_A, DOC_B]} />)
    await user.click(screen.getByRole('checkbox', { name: 'Chọn Thông báo A' }))
    await user.click(screen.getByRole('checkbox', { name: 'Chọn Thông báo B' }))
    expect(screen.getByRole('checkbox', { name: 'Chọn Thông báo A' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: 'Chọn Thông báo B' })).toBeChecked()
    await user.click(screen.getByRole('checkbox', { name: 'Chọn Thông báo A' }))
    expect(screen.getByRole('checkbox', { name: 'Chọn Thông báo A' })).not.toBeChecked()
    expect(screen.getByRole('checkbox', { name: 'Chọn Thông báo B' })).toBeChecked()
  })

  it('pressing Enter on a row checkbox does not open the row', async () => {
    const user = userEvent.setup()
    const onOpenDocument = vi.fn()
    render(<Harness children={[]} documents={[DOC_A]} onOpenDocument={onOpenDocument} />)
    screen.getByRole('checkbox', { name: 'Chọn Thông báo A' }).focus()
    await user.keyboard('{Enter}')
    expect(onOpenDocument).not.toHaveBeenCalled()
  })

  it('header checkbox: none → select all folders + documents; partial shows indeterminate; all → clears', async () => {
    const user = userEvent.setup()
    render(<Harness children={[FOLDER]} documents={[DOC_A, DOC_B]} />)
    const header = screen.getByRole('checkbox', { name: 'Chọn tất cả' })
    expect(header).not.toBeChecked()

    await user.click(screen.getByRole('checkbox', { name: 'Chọn Thông báo A' }))
    expect(header).toHaveAttribute('data-state', 'indeterminate')

    await user.click(header)
    for (const name of ['Chọn Phụ lục', 'Chọn Thông báo A', 'Chọn Thông báo B']) {
      expect(screen.getByRole('checkbox', { name })).toBeChecked()
    }
    expect(header).toBeChecked()

    await user.click(header)
    for (const name of ['Chọn Phụ lục', 'Chọn Thông báo A', 'Chọn Thông báo B']) {
      expect(screen.getByRole('checkbox', { name })).not.toBeChecked()
    }
  })

  it('Ctrl+click selects a row without opening it', async () => {
    const user = userEvent.setup()
    const onOpenDocument = vi.fn()
    render(<Harness children={[]} documents={[DOC_A, DOC_B]} onOpenDocument={onOpenDocument} />)
    const row = screen.getByRole('button', { name: 'Thông báo A' })
    await user.keyboard('{Control>}')
    await user.click(row)
    await user.keyboard('{/Control}')
    expect(row).toHaveAttribute('data-selected', 'true')
    expect(onOpenDocument).not.toHaveBeenCalled()
  })

  it('Ctrl+bấm dòng thứ hai → GIỮ dòng đầu, thêm dòng thứ hai vào lượt chọn', async () => {
    const user = userEvent.setup()
    render(<Harness children={[]} documents={[DOC_A, DOC_B]} />)
    await user.keyboard('{Control>}')
    await user.click(screen.getByRole('button', { name: 'Thông báo A' }))
    await user.click(screen.getByRole('button', { name: 'Thông báo B' }))
    await user.keyboard('{/Control}')
    expect(screen.getByRole('button', { name: 'Thông báo A' })).toHaveAttribute(
      'data-selected',
      'true',
    )
    expect(screen.getByRole('button', { name: 'Thông báo B' })).toHaveAttribute(
      'data-selected',
      'true',
    )
  })

  it('plain click on a folder row opens that folder id', async () => {
    const user = userEvent.setup()
    const onOpenFolder = vi.fn()
    render(<Harness children={[FOLDER]} documents={[]} onOpenFolder={onOpenFolder} />)
    await user.click(screen.getByRole('button', { name: 'Phụ lục' }))
    expect(onOpenFolder).toHaveBeenCalledTimes(1)
    expect(onOpenFolder).toHaveBeenCalledWith(5)
  })

  //  Radix `ContextMenu` (chuột phải) không có mẫu kiểm THẬT nào trong cả repo
  //  (dựa vào `contextmenu`/pointer-capture native, không ổn định trên jsdom)
  //  — kiểm qua nút «⋯» LUÔN THẤY (`showMenuButton`), cùng danh sách mục với
  //  chuột phải (`buildFolderItemMenuActions`, xem `folder-item-context-menu.tsx`).
  //  Mỗi bài chỉ dựng ĐÚNG MỘT dòng nên "Thêm tùy chọn" không trùng tên.
  it('nút «⋯» của một dòng văn bản có mục «Mở»/«Xem chi tiết»', async () => {
    const user = userEvent.setup()
    render(<Harness children={[]} documents={[DOC_A]} />)
    await user.click(screen.getByRole('button', { name: 'Thêm tùy chọn' }))
    expect(await screen.findByRole('menuitem', { name: 'Mở' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Xem chi tiết' })).toBeInTheDocument()
  })

  it('nút «⋯» của một dòng thư mục QUẢN LÝ có đủ Đổi tên/Chuyển tới/Chia sẻ/Xóa', async () => {
    const user = userEvent.setup()
    render(<Harness children={[FOLDER]} documents={[]} />)
    await user.click(screen.getByRole('button', { name: 'Thêm tùy chọn' }))
    expect(await screen.findByRole('menuitem', { name: 'Đổi tên' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Chuyển tới…' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Chia sẻ…' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: /^Xóa/ })).toBeInTheDocument()
  })

  //  Gốc «Thư mục của bạn» (`folder-my-drive-panel.tsx`, duoc-CR-476) dùng lại
  //  chế độ Danh sách để vẽ thư mục PHÁP NHÂN — dòng đó phải truyền đúng
  //  `isCompanyRoot` cho `FolderItemContextMenu`.
  it('company folder row offers Rename and Move like any folder', async () => {
    //  Luật cũ (ẩn với thư mục pháp nhân) BỎ 24/09/2026 — đại ca chốt thư mục pháp
    //  nhân chỉ là thư mục thường: đổi tên, chuyển đâu cũng được.
    const user = userEvent.setup()
    const companyRoot: DocFolderTreeNode = {
      ...FOLDER,
      id: 1,
      kind: FOLDER_KIND.company,
      kind_label: 'Thư mục pháp nhân',
      name: 'CÔNG TY A',
      parent_id: 0,
      path: '/1/',
      depth: 0,
    }
    render(<Harness children={[companyRoot]} documents={[]} />)
    await user.click(screen.getByRole('button', { name: 'Thêm tùy chọn' }))
    expect(await screen.findByRole('menuitem', { name: 'Đổi tên' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Chuyển tới…' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Chia sẻ…' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Xem chi tiết' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: /^Xóa/ })).toBeInTheDocument()
  })
})
