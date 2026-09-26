import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import type * as ReactRouterDom from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { FOLDER_DRAG_MIME, writeFolderDragPayload } from '../helpers/folder-drag-payload'
import {
  useArchiveDocFolder,
  useCreateDocFolder,
  useDeleteDocFolder,
  useDocFolderTree,
  useLinkDocumentsToFolder,
  useMoveDocFolder,
  useReorderDocFolders,
  useUnlinkDocumentsFromFolder,
  useUpdateDocFolder,
} from '../hooks/use-document-folders'
import { useFolderTreeDocumentLeaves } from '../hooks/use-folder-tree-document-leaves'
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND, FOLDER_STATUS } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'
import type { DocumentRecord } from '../types/document-record'
import { FolderTreePanel } from './folder-tree-panel'

const navigate = vi.fn()
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof ReactRouterDom>()
  return { ...actual, useNavigate: () => navigate }
})
vi.mock('sonner', () => ({ toast: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }))
//  Vai trò mặc định ĐỦ quyền tạo thư mục/văn bản — bài nào cần người chỉ xem
//  thì đặt `canCreateFolder = false` (trần theo vai trò, test UI 24/09/2026).
let canCreateFolder = true
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) =>
      entity === 'doc_folder' && action === 'create' ? canCreateFolder : true,
  }),
}))
//  Không có văn bản nào để nạp trong PHẦN LỚN bài kiểm ở đây (không đụng tới lá
//  văn bản) — mặc định trả Map rỗng, khỏi cần dựng `QueryClientProvider` thật
//  cho một `useQueries` không ai kiểm. `vi.fn()` (không phải arrow trần) để
//  vài bài kiểm RIÊNG (điều hướng lá văn bản, tắt «Hiện văn bản trong cây») tự
//  đổi `mockReturnValue`/kiểm tra được đối số gọi vào.
vi.mock('../hooks/use-folder-tree-document-leaves', () => ({
  useFolderTreeDocumentLeaves: vi.fn(() => new Map()),
}))
vi.mock('../hooks/use-document-folders', () => ({
  useDocFolderTree: vi.fn(),
  useCreateDocFolder: vi.fn(),
  useUpdateDocFolder: vi.fn(),
  useArchiveDocFolder: vi.fn(),
  useDeleteDocFolder: vi.fn(),
  useMoveDocFolder: vi.fn(),
  useReorderDocFolders: vi.fn(),
  useLinkDocumentsToFolder: vi.fn(),
  useUnlinkDocumentsFromFolder: vi.fn(),
}))

function folderRow(overrides: Partial<DocFolderTreeNode> & { id: number }): DocFolderTreeNode {
  return {
    company_id: 1,
    parent_id: 0,
    kind: FOLDER_KIND.normal,
    kind_label: 'Thư mục',
    name: `Thư mục ${overrides.id}`,
    code: '',
    path: `/${overrides.id}/`,
    depth: 1,
    sort_order: 0,
    status: FOLDER_STATUS.active,
    status_label: 'Đang dùng',
    document_count: 0,
    document_count_branch: 0,
    my_level: FOLDER_ACCESS_LEVEL.manage,
    ...overrides,
  }
}

const ROOT = folderRow({
  id: 1,
  kind: FOLDER_KIND.company,
  parent_id: 0,
  path: '/1/',
  depth: 0,
  name: 'CÔNG TY',
})
const CONTRACTS = folderRow({
  id: 2,
  parent_id: 1,
  path: '/1/2/',
  depth: 1,
  name: 'Hợp đồng',
  document_count_branch: 5,
})
const SUB = folderRow({ id: 3, parent_id: 2, path: '/1/2/3/', depth: 2, name: 'Con của Hợp đồng' })

/** `mutate` giả GỌI NGAY `onSuccess` — đủ cho bài kiểm không cần `waitFor` async thật. */
function mockMutation<TVars, TResult>(result: TResult) {
  const mutate = vi.fn(
    (
      _variables: TVars,
      options?: { onSuccess?: (data: TResult) => void; onError?: () => void },
    ) => {
      options?.onSuccess?.(result)
    },
  )
  return { mutate, isPending: false, mutateAsync: vi.fn().mockResolvedValue(result) }
}

let createMutate: ReturnType<typeof vi.fn>
let updateMutate: ReturnType<typeof vi.fn>
let linkMutate: ReturnType<typeof vi.fn>

beforeEach(() => {
  canCreateFolder = true
  navigate.mockReset()
  localStorage.clear()
  //  Mở sẵn CÔNG TY(1) và Hợp đồng(2) — mô phỏng người dùng đã bấm vào tới đó ở
  //  phiên trước (`expandedIds` nhớ qua `localStorage`, xem `folder-tree-panel.tsx`).
  //  Không mở thì mọi dòng dưới depth 0 không đứng trong DOM để bài kiểm tìm tới.
  localStorage.setItem('erp.document.folders.expanded', JSON.stringify([1, 2]))
  vi.mocked(useFolderTreeDocumentLeaves).mockReturnValue(new Map())
  vi.mocked(useDocFolderTree).mockReturnValue({
    data: [ROOT, CONTRACTS, SUB],
    isLoading: false,
    isFetching: false,
    refetch: vi.fn(),
  } as unknown as ReturnType<typeof useDocFolderTree>)

  const created = folderRow({ id: 99, parent_id: 2, name: 'Vừa tạo' })
  const create = mockMutation(created)
  createMutate = create.mutate
  vi.mocked(useCreateDocFolder).mockReturnValue(
    create as unknown as ReturnType<typeof useCreateDocFolder>,
  )

  const update = mockMutation(CONTRACTS)
  updateMutate = update.mutate
  vi.mocked(useUpdateDocFolder).mockReturnValue(
    update as unknown as ReturnType<typeof useUpdateDocFolder>,
  )

  vi.mocked(useArchiveDocFolder).mockReturnValue(
    mockMutation(CONTRACTS) as unknown as ReturnType<typeof useArchiveDocFolder>,
  )
  vi.mocked(useDeleteDocFolder).mockReturnValue(
    mockMutation(null) as unknown as ReturnType<typeof useDeleteDocFolder>,
  )
  vi.mocked(useMoveDocFolder).mockReturnValue(
    mockMutation(CONTRACTS) as unknown as ReturnType<typeof useMoveDocFolder>,
  )
  vi.mocked(useReorderDocFolders).mockReturnValue(
    mockMutation({ changed: 0 }) as unknown as ReturnType<typeof useReorderDocFolders>,
  )
  const link = mockMutation({ moved: [], denied: [] })
  linkMutate = link.mutate
  vi.mocked(useLinkDocumentsToFolder).mockReturnValue(
    link as unknown as ReturnType<typeof useLinkDocumentsToFolder>,
  )
  vi.mocked(useUnlinkDocumentsFromFolder).mockReturnValue(
    mockMutation({ moved: [], denied: [] }) as unknown as ReturnType<
      typeof useUnlinkDocumentsFromFolder
    >,
  )
})

function renderPanel(selectedFolderId: number | null = 2, onSelectDocument = vi.fn()) {
  return render(
    <MemoryRouter>
      <FolderTreePanel
        selectedFolderId={selectedFolderId}
        onSelectFolder={vi.fn()}
        onSelectDocument={onSelectDocument}
        onOpenAccessTab={vi.fn()}
      />
    </MemoryRouter>,
  )
}

describe('FolderTreePanel — đường gióng thụt lề theo cấp', () => {
  it('thư mục cấp 2 (Con của Hợp đồng, depth=2) có đúng 2 đường gióng', () => {
    renderPanel()
    const row = screen.getByRole('treeitem', { name: /Con của Hợp đồng/ })
    const guide = row.querySelector('[data-tree-indent-guide]')
    expect(guide?.getAttribute('data-tree-indent-levels')).toBe('2')
  })
})

describe('FolderTreePanel — đổi tên tại chỗ (F2 · Enter · Esc · blur)', () => {
  it('F2 trên thư mục đang chọn mở ô nhập, Enter lưu gọi update với tên mới', async () => {
    const user = userEvent.setup()
    renderPanel(2)
    const row = screen.getByRole('treeitem', { name: /^Hợp đồng/ })
    row.focus()
    await user.keyboard('{F2}')

    const input = screen.getByLabelText('Đổi tên Hợp đồng')
    await user.clear(input)
    await user.type(input, 'Hợp đồng mới{Enter}')

    expect(updateMutate).toHaveBeenCalledWith({ id: 2, payload: { name: 'Hợp đồng mới' } })
    expect(screen.queryByLabelText('Đổi tên Hợp đồng')).not.toBeInTheDocument()
  })

  it('Esc hủy — không gọi update, ô nhập biến mất', async () => {
    const user = userEvent.setup()
    renderPanel(2)
    screen.getByRole('treeitem', { name: /^Hợp đồng/ }).focus()
    await user.keyboard('{F2}')
    const input = screen.getByLabelText('Đổi tên Hợp đồng')
    await user.type(input, 'x')
    await user.keyboard('{Escape}')

    expect(updateMutate).not.toHaveBeenCalled()
    expect(screen.queryByLabelText('Đổi tên Hợp đồng')).not.toBeInTheDocument()
  })

  it('mất focus (blur) cũng LƯU như Enter', async () => {
    const user = userEvent.setup()
    renderPanel(2)
    screen.getByRole('treeitem', { name: /^Hợp đồng/ }).focus()
    await user.keyboard('{F2}')
    const input = screen.getByLabelText('Đổi tên Hợp đồng')
    await user.clear(input)
    await user.type(input, 'Đổi qua blur')
    input.blur()

    expect(updateMutate).toHaveBeenCalledWith({ id: 2, payload: { name: 'Đổi qua blur' } })
  })

  it('bấm đúp một dòng đủ quyền Quản lý cũng mở ô đổi tên tại chỗ', async () => {
    const user = userEvent.setup()
    renderPanel(2)
    await user.dblClick(screen.getByRole('treeitem', { name: /^Hợp đồng/ }))
    expect(screen.getByLabelText('Đổi tên Hợp đồng')).toBeInTheDocument()
  })
})

describe('FolderTreePanel — dòng tạm «thư mục mới» (không mở hộp thoại)', () => {
  it('bấm "Thư mục mới" ở tiêu đề mở dòng nhập NGAY dưới thư mục đang chọn, Enter tạo đúng cha', async () => {
    const user = userEvent.setup()
    renderPanel(2)

    await user.click(screen.getByRole('button', { name: 'Thư mục mới' }))
    const input = screen.getByLabelText('Tên thư mục mới')
    expect(input).toHaveAttribute('placeholder', 'Tên thư mục mới…')

    await user.type(input, 'Phụ lục{Enter}')

    expect(createMutate).toHaveBeenCalledWith({ parent_id: 2, name: 'Phụ lục' }, expect.anything())
    //  Không có hộp thoại nào được dựng — chỉ còn ô nhập tại chỗ, và nó đã đóng lại.
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Tên thư mục mới')).not.toBeInTheDocument()
  })

  it('gõ rồi Esc thì HỦY, không gọi tạo', async () => {
    const user = userEvent.setup()
    renderPanel(2)
    await user.click(screen.getByRole('button', { name: 'Thư mục mới' }))
    const input = screen.getByLabelText('Tên thư mục mới')
    await user.type(input, 'bỏ dở')
    await user.keyboard('{Escape}')

    expect(createMutate).not.toHaveBeenCalled()
    expect(screen.queryByLabelText('Tên thư mục mới')).not.toBeInTheDocument()
  })

  it('rời ô mà để TRỐNG thì HỦY luôn, không tạo bản ghi rỗng', async () => {
    const user = userEvent.setup()
    renderPanel(2)
    await user.click(screen.getByRole('button', { name: 'Thư mục mới' }))
    const input = screen.getByLabelText('Tên thư mục mới')
    input.blur()

    expect(createMutate).not.toHaveBeenCalled()
  })

  //  Ở GỐC tạo được thư mục tự do (mở 24/09/2026) — chỉ khóa khi vai trò
  //  thiếu `doc_folder.create`.
  it('chưa chọn thư mục nào và thiếu doc_folder.create thì nút "Thư mục mới" bị khóa', () => {
    canCreateFolder = false
    renderPanel(null)
    expect(screen.getByRole('button', { name: 'Thư mục mới' })).toBeDisabled()
  })

  it('nút "+" hiện trên dòng cây (renderHoverActions) cũng mở đúng dòng tạm dưới ĐÚNG cha đó', async () => {
    const user = userEvent.setup()
    renderPanel(null)
    await user.click(screen.getByRole('button', { name: 'Thêm thư mục con vào Hợp đồng' }))
    await user.type(screen.getByLabelText('Tên thư mục mới'), 'Con mới{Enter}')
    expect(createMutate).toHaveBeenCalledWith({ parent_id: 2, name: 'Con mới' }, expect.anything())
  })

  //  Test UI 24/09/2026: mức Đóng góp của thư mục pháp nhân có thể đến từ quyền
  //  GHI văn bản — người đó KHÔNG tạo được thư mục, nên không được thấy nút "+".
  it('hides the "+" add-subfolder button when the role lacks doc_folder.create', () => {
    canCreateFolder = false
    renderPanel(null)
    expect(
      screen.queryByRole('button', { name: 'Thêm thư mục con vào Hợp đồng' }),
    ).not.toBeInTheDocument()
  })
})

describe('FolderTreePanel — Thu gọn tất cả', () => {
  it('bấm "Thu gọn tất cả" thì gập MỌI cấp — chỉ còn dòng gốc, cả cháu lẫn con đều biến mất', async () => {
    const user = userEvent.setup()
    renderPanel(2)
    expect(screen.getByRole('treeitem', { name: /Con của Hợp đồng/ })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Thu gọn tất cả' }))

    expect(screen.queryByRole('treeitem', { name: /Con của Hợp đồng/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('treeitem', { name: /^Hợp đồng/ })).not.toBeInTheDocument()
    expect(screen.getByRole('treeitem', { name: /^CÔNG TY/ })).toHaveAttribute(
      'aria-expanded',
      'false',
    )
  })
})

describe('FolderTreePanel — nhận thả payload từ khung phải', () => {
  function dropPayload(payload: {
    documentIds: number[]
    folderIds: number[]
    sourceFolderId: number | null
  }) {
    const dataTransfer = {
      setData: vi.fn(),
      getData: vi.fn(),
      types: [FOLDER_DRAG_MIME],
    } as unknown as DataTransfer
    writeFolderDragPayload(dataTransfer, payload)
    const written = (dataTransfer.setData as ReturnType<typeof vi.fn>).mock.calls[0]?.[1] as string
    ;(dataTransfer.getData as ReturnType<typeof vi.fn>).mockReturnValue(written)
    return dataTransfer
  }

  it('thả văn bản lên một dòng thư mục gọi linkDocuments đúng folder_id của dòng đó', async () => {
    renderPanel(null)
    const row = screen.getByRole('treeitem', { name: /^Hợp đồng/ })
    const { fireEvent } = await import('@testing-library/react')
    fireEvent.drop(row, {
      dataTransfer: dropPayload({ documentIds: [7], folderIds: [], sourceFolderId: null }),
    })

    expect(linkMutate).toHaveBeenCalledWith(
      { document_ids: [7], folder_id: 2, mode: 'add' },
      expect.anything(),
    )
  })
})

describe('FolderTreePanel — trạng thái rỗng', () => {
  it('không có thư mục nào thì báo rõ, không tự nổ', () => {
    vi.mocked(useDocFolderTree).mockReturnValue({
      data: [],
      isLoading: false,
      isFetching: false,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useDocFolderTree>)
    renderPanel(null)
    expect(screen.getByText('Chưa có thư mục nào.')).toBeInTheDocument()
  })
})

describe('FolderTreePanel — không rò aria-label trùng nhau', () => {
  it('cả cây chỉ có đúng một dòng mang tên "Hợp đồng"', () => {
    renderPanel(2)
    const tree = screen.getByRole('tree', { name: 'Cây thư mục văn bản' })
    expect(within(tree).getAllByText('Hợp đồng')).toHaveLength(1)
  })
})

describe('FolderTreePanel — bấm dòng thư mục vs bấm chevron (đặc tả §3, duoc-CR-476)', () => {
  it('bấm dòng thư mục (không phải chevron) → gọi onSelectFolder', async () => {
    const user = userEvent.setup()
    const onSelectFolder = vi.fn()
    render(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={null}
          onSelectFolder={onSelectFolder}
          onSelectDocument={vi.fn()}
          onOpenAccessTab={vi.fn()}
        />
      </MemoryRouter>,
    )
    await user.click(screen.getByRole('treeitem', { name: /^Hợp đồng/ }))
    expect(onSelectFolder).toHaveBeenCalledWith(2)
  })

  it('bấm CHEVRON của dòng có con → chỉ mở/gập, KHÔNG gọi onSelectFolder', async () => {
    const user = userEvent.setup()
    const onSelectFolder = vi.fn()
    render(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={null}
          onSelectFolder={onSelectFolder}
          onSelectDocument={vi.fn()}
          onOpenAccessTab={vi.fn()}
        />
      </MemoryRouter>,
    )
    const row = screen.getByRole('treeitem', { name: /^Hợp đồng/ })
    //  Hợp đồng(2) đã MỞ sẵn (localStorage [1,2]) và có con SUB(3) → chevron đang ở trạng thái "Thu gọn".
    await user.click(within(row).getByRole('button', { name: 'Thu gọn' }))
    expect(onSelectFolder).not.toHaveBeenCalled()
    expect(row).toHaveAttribute('aria-expanded', 'false')
  })

  //  Dòng GỐC pháp nhân (CÔNG TY, kind=company) đi qua ĐÚNG nhánh `else` của
  //  `handleSelect` (`use-folder-tree-navigation.ts`) như mọi thư mục thường —
  //  không có nhánh riêng nào loại trừ `kind === company` khỏi việc MỞ bằng
  //  một cú bấm. Bài kiểm này CHỐT LẠI hành vi đó bằng tên (yêu cầu 24/09/2026:
  //  "bấm một lần vào dòng cây phải mở thư mục", kể cả dòng gốc).
  it('bấm dòng GỐC PHÁP NHÂN (CÔNG TY) → cũng gọi onSelectFolder đúng id, không cần bấm đúp', async () => {
    const user = userEvent.setup()
    const onSelectFolder = vi.fn()
    render(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={null}
          onSelectFolder={onSelectFolder}
          onSelectDocument={vi.fn()}
          onOpenAccessTab={vi.fn()}
        />
      </MemoryRouter>,
    )
    await user.click(screen.getByRole('treeitem', { name: /^CÔNG TY/ }))
    expect(onSelectFolder).toHaveBeenCalledWith(1)
  })

  it('bấm CHEVRON của dòng GỐC PHÁP NHÂN → chỉ mở/gập, KHÔNG gọi onSelectFolder', async () => {
    const user = userEvent.setup()
    const onSelectFolder = vi.fn()
    render(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={null}
          onSelectFolder={onSelectFolder}
          onSelectDocument={vi.fn()}
          onOpenAccessTab={vi.fn()}
        />
      </MemoryRouter>,
    )
    const row = screen.getByRole('treeitem', { name: /^CÔNG TY/ })
    //  CÔNG TY(1) đã MỞ sẵn (localStorage [1,2]) → chevron đang ở trạng thái "Thu gọn".
    await user.click(within(row).getByRole('button', { name: 'Thu gọn' }))
    expect(onSelectFolder).not.toHaveBeenCalled()
    expect(row).toHaveAttribute('aria-expanded', 'false')
  })
})

describe('FolderTreePanel — bấm/kích hoạt LÁ VĂN BẢN (đặc tả §3, duoc-CR-476)', () => {
  const DOC = {
    id: 77,
    title: 'Tài liệu X',
    status: 1,
    effective_date: null,
    expire_date: null,
    display_code: 'DEGO-001',
  } as unknown as DocumentRecord

  beforeEach(() => {
    //  Hợp đồng(2) đã mở sẵn (localStorage [1,2]) — lá văn bản chèn thêm dưới nó.
    vi.mocked(useFolderTreeDocumentLeaves).mockReturnValue(
      new Map([[2, { documents: [DOC], total: 1, isLoading: false }]]),
    )
  })

  it('bấm MỘT LẦN → chọn văn bản ở khung phải qua onSelectDocument, KHÔNG điều hướng rời trang', async () => {
    const user = userEvent.setup()
    const onSelectDocument = vi.fn()
    render(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={null}
          onSelectFolder={vi.fn()}
          onSelectDocument={onSelectDocument}
          onOpenAccessTab={vi.fn()}
        />
      </MemoryRouter>,
    )
    await user.click(screen.getByRole('treeitem', { name: 'Tài liệu X' }))
    expect(onSelectDocument).toHaveBeenCalledWith(2, 77)
    expect(navigate).not.toHaveBeenCalled()
  })

  it('bấm ĐÚP → mở thẳng trang chi tiết văn bản (điều hướng, không chỉ chọn)', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={null}
          onSelectFolder={vi.fn()}
          onSelectDocument={vi.fn()}
          onOpenAccessTab={vi.fn()}
        />
      </MemoryRouter>,
    )
    await user.dblClick(screen.getByRole('treeitem', { name: 'Tài liệu X' }))
    expect(navigate).toHaveBeenCalledWith('/document/documents/77')
  })

  it('Enter (bàn phím) trên dòng đang focus → cũng mở thẳng trang chi tiết, cùng nghĩa bấm đúp', async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={null}
          onSelectFolder={vi.fn()}
          onSelectDocument={vi.fn()}
          onOpenAccessTab={vi.fn()}
        />
      </MemoryRouter>,
    )
    screen.getByRole('treeitem', { name: 'Tài liệu X' }).focus()
    await user.keyboard('{Enter}')
    expect(navigate).toHaveBeenCalledWith('/document/documents/77')
  })
})

describe('FolderTreePanel — «Hiện văn bản trong cây» (đặc tả §2, duoc-CR-476)', () => {
  it('mặc định BẬT — vẫn gọi nạp lá cho thư mục đang mở', () => {
    renderPanel(null)
    expect(useFolderTreeDocumentLeaves).toHaveBeenCalledWith(expect.arrayContaining([2]))
  })

  it('tắt công tắc trong menu ⋯ → KHÔNG còn gọi nạp lá (mảng rỗng), dù thư mục vẫn đang mở', async () => {
    const user = userEvent.setup()
    renderPanel(null)
    vi.mocked(useFolderTreeDocumentLeaves).mockClear()

    await user.click(screen.getByRole('button', { name: 'Thêm tùy chọn' }))
    await user.click(screen.getByRole('menuitemcheckbox', { name: 'Hiện văn bản trong cây' }))

    expect(useFolderTreeDocumentLeaves).toHaveBeenLastCalledWith([])
  })
})

describe('FolderTreePanel — thư mục ĐANG CHỌN đổi từ ngoài tự lộ ra trên cây (đặc tả §4, sync cây ⇄ nội dung)', () => {
  it('`selectedFolderId` đổi sang một nhánh đang GẬP → tự mở đủ tổ tiên rồi tô sáng đúng dòng', () => {
    //  Gập hết trước khi dựng — không nạp sẵn [1,2] như mặc định.
    localStorage.setItem('erp.document.folders.expanded', JSON.stringify([]))
    const { rerender } = render(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={null}
          onSelectFolder={vi.fn()}
          onSelectDocument={vi.fn()}
          onOpenAccessTab={vi.fn()}
        />
      </MemoryRouter>,
    )
    expect(screen.queryByRole('treeitem', { name: /^Hợp đồng/ })).not.toBeInTheDocument()

    rerender(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={2}
          onSelectFolder={vi.fn()}
          onSelectDocument={vi.fn()}
          onOpenAccessTab={vi.fn()}
        />
      </MemoryRouter>,
    )

    const row = screen.getByRole('treeitem', { name: /^Hợp đồng/ })
    expect(row).toBeInTheDocument()
    expect(row).toHaveAttribute('aria-selected', 'true')
  })
  //  Lỗi người dùng báo 24/09/2026: bấm thư mục ở khung phải → cây tô sáng
  //  đúng dòng nhưng dòng đó vẫn GẬP, không thấy bên trong có gì.
  it('also expands the selected folder ITSELF so its children show in the tree', () => {
    localStorage.setItem('erp.document.folders.expanded', JSON.stringify([]))
    renderPanel(2)
    expect(screen.getByRole('treeitem', { name: /^Hợp đồng/ })).toHaveAttribute(
      'aria-expanded',
      'true',
    )
    expect(screen.getByRole('treeitem', { name: /^Con của Hợp đồng/ })).toBeInTheDocument()
  })
})

//  Phản hồi 24/09/2026: lỡ bấm vào một pháp nhân là KẸT, cây không còn chỗ nào
//  để quay về gốc — «+ Mới» cứ tạo vào pháp nhân đó.
describe('FolderTreePanel — về gốc «Thư mục của bạn»', () => {
  it('clicking the «Thư mục» header label calls onSelectRoot', async () => {
    const user = userEvent.setup()
    const onSelectRoot = vi.fn()
    render(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={2}
          onSelectFolder={vi.fn()}
          onSelectDocument={vi.fn()}
          onOpenAccessTab={vi.fn()}
          onSelectRoot={onSelectRoot}
        />
      </MemoryRouter>,
    )
    await user.click(screen.getByRole('button', { name: 'Thư mục' }))
    expect(onSelectRoot).toHaveBeenCalledTimes(1)
  })

  it('marks the root label as current only when no folder is selected', () => {
    const { rerender } = render(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={null}
          onSelectFolder={vi.fn()}
          onSelectDocument={vi.fn()}
          onOpenAccessTab={vi.fn()}
          onSelectRoot={vi.fn()}
        />
      </MemoryRouter>,
    )
    expect(screen.getByRole('button', { name: 'Thư mục' })).toHaveAttribute('aria-current', 'page')
    rerender(
      <MemoryRouter>
        <FolderTreePanel
          selectedFolderId={2}
          onSelectFolder={vi.fn()}
          onSelectDocument={vi.fn()}
          onOpenAccessTab={vi.fn()}
          onSelectRoot={vi.fn()}
        />
      </MemoryRouter>,
    )
    expect(screen.getByRole('button', { name: 'Thư mục' })).not.toHaveAttribute('aria-current')
  })
})
