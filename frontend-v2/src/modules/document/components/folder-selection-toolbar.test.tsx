import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { toast } from 'sonner'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { usePermission } from '@/core/authorization/use-permission'
import { confirm } from '@/shared/ui/confirm-dialog'
import {
  FolderSelectionToolbar,
  MAX_BULK_DOCUMENT_IDS,
  MAX_BULK_FOLDER_IDS,
} from './folder-selection-toolbar'
import type * as UseDocumentFolders from '../hooks/use-document-folders'
import {
  useDeleteDocFolder,
  useLinkDocumentsToFolder,
  useMoveDocFolder,
  useUnlinkDocumentsFromFolder,
} from '../hooks/use-document-folders'
import { useDeleteDocument } from '../hooks/use-documents'

vi.mock('sonner', () => ({ toast: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }))
vi.mock('../hooks/use-document-folders', async (importOriginal) => {
  const actual = await importOriginal<typeof UseDocumentFolders>()
  return {
    ...actual,
    useLinkDocumentsToFolder: vi.fn(),
    useUnlinkDocumentsFromFolder: vi.fn(),
    useMoveDocFolder: vi.fn(),
    useDeleteDocFolder: vi.fn(),
    useDocFolderTree: vi.fn(() => ({ data: [] })),
    useDocFolderSearch: vi.fn(() => ({ data: [] })),
    useCreateDocFolder: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  }
})
vi.mock('../hooks/use-documents', () => ({ useDeleteDocument: vi.fn() }))
vi.mock('@/core/authorization/use-permission', () => ({ usePermission: vi.fn() }))
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: vi.fn() }))

const CURRENT_FOLDER = { id: 5, name: 'Hợp đồng' }

const unlinkMutate = vi.fn()
const linkMutate = vi.fn()
const moveMutate = vi.fn()
const deleteFolderMutate = vi.fn()
const deleteDocumentMutate = vi.fn()

beforeEach(() => {
  unlinkMutate.mockReset()
  linkMutate.mockReset()
  moveMutate.mockReset()
  deleteFolderMutate.mockReset()
  deleteDocumentMutate.mockReset()
  vi.mocked(toast.success).mockClear()
  vi.mocked(useUnlinkDocumentsFromFolder).mockReturnValue({ mutate: unlinkMutate } as unknown as ReturnType<
    typeof useUnlinkDocumentsFromFolder
  >)
  vi.mocked(useLinkDocumentsToFolder).mockReturnValue({ mutate: linkMutate } as unknown as ReturnType<
    typeof useLinkDocumentsToFolder
  >)
  vi.mocked(useMoveDocFolder).mockReturnValue({ mutate: moveMutate } as unknown as ReturnType<
    typeof useMoveDocFolder
  >)
  vi.mocked(useDeleteDocFolder).mockReturnValue({ mutate: deleteFolderMutate } as unknown as ReturnType<
    typeof useDeleteDocFolder
  >)
  vi.mocked(useDeleteDocument).mockReturnValue({ mutate: deleteDocumentMutate } as unknown as ReturnType<
    typeof useDeleteDocument
  >)
  //  Mặc định KHÔNG có quyền xóa văn bản — đúng hành vi cũ trước khi thêm nút
  //  «Xóa» (các bài kiểm HIỆN CÓ ở dưới không quan tâm tới quyền này).
  vi.mocked(usePermission).mockReturnValue({ can: () => false } as unknown as ReturnType<typeof usePermission>)
  vi.mocked(confirm).mockResolvedValue(true)
})

describe('FolderSelectionToolbar — hiện/ẩn theo thành phần lượt chọn', () => {
  it('không chọn gì → không dựng gì cả', () => {
    const { container } = render(
      <FolderSelectionToolbar
        selectedFolderIds={[]}
        selectedDocumentIds={[]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={vi.fn()}
      />,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('chỉ chọn văn bản: đủ cả ba nút icon Thêm/Chuyển/Gỡ, kèm tooltip đúng chữ', () => {
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[]}
        selectedDocumentIds={[1, 2]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={vi.fn()}
      />,
    )
    expect(screen.getByText('2 mục đã chọn')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Thêm vào thư mục' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Chuyển tới' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Gỡ khỏi «Hợp đồng»' })).toBeInTheDocument()
  })

  it('có LẪN thư mục trong lượt chọn: ẩn Thêm vào thư mục / Gỡ khỏi, chỉ còn Chuyển tới', () => {
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[9]}
        selectedDocumentIds={[1]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={vi.fn()}
      />,
    )
    expect(screen.getByText('2 mục đã chọn')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Thêm vào thư mục' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Gỡ khỏi/ })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Chuyển tới' })).toBeInTheDocument()
  })
})

describe('FolderSelectionToolbar — hành động + kết quả báo qua toast', () => {
  it('bấm «Gỡ khỏi» gọi unlink đúng payload, báo kết quả qua toast, rồi tự bỏ chọn', async () => {
    const user = userEvent.setup()
    const onClear = vi.fn()
    unlinkMutate.mockImplementation((_payload, opts) => {
      opts.onSuccess({ moved: [1, 2], denied: [] })
    })

    render(
      <FolderSelectionToolbar
        selectedFolderIds={[]}
        selectedDocumentIds={[1, 2]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={onClear}
        onShowDetails={vi.fn()}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'Gỡ khỏi «Hợp đồng»' }))

    expect(unlinkMutate).toHaveBeenCalledWith(
      { document_ids: [1, 2], folder_id: 5 },
      expect.anything(),
    )
    expect(toast.success).toHaveBeenCalledWith('Đã gỡ 2 · bị từ chối 0')
    expect(onClear).toHaveBeenCalledOnce()
  })

  it('bấm nút «Chi tiết» gọi onShowDetails', async () => {
    const user = userEvent.setup()
    const onShowDetails = vi.fn()
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[]}
        selectedDocumentIds={[1]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={onShowDetails}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'Chi tiết' }))
    expect(onShowDetails).toHaveBeenCalledOnce()
  })

  it('bấm nút bỏ chọn (✕ đầu bảng) gọi onClearSelection', async () => {
    const user = userEvent.setup()
    const onClear = vi.fn()
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[]}
        selectedDocumentIds={[1]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={onClear}
        onShowDetails={vi.fn()}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'Bỏ chọn' }))
    expect(onClear).toHaveBeenCalledOnce()
  })
})

describe('FolderSelectionToolbar — trần chọn hàng loạt', () => {
  it(`vượt trần ${MAX_BULK_DOCUMENT_IDS} văn bản → cảnh báo icon hiện, ba nút hành động bị TẮT`, () => {
    const many = Array.from({ length: MAX_BULK_DOCUMENT_IDS + 1 }, (_, i) => i + 1)
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[]}
        selectedDocumentIds={many}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={vi.fn()}
      />,
    )
    expect(screen.getByLabelText('Vượt trần thao tác hàng loạt')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Thêm vào thư mục' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Chuyển tới' })).toBeDisabled()
    expect(screen.getByRole('button', { name: /Gỡ khỏi/ })).toBeDisabled()
  })

  it(`đúng trần (không vượt) thì KHÔNG báo lỗi, nút vẫn bật`, () => {
    const exactly = Array.from({ length: MAX_BULK_DOCUMENT_IDS }, (_, i) => i + 1)
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[]}
        selectedDocumentIds={exactly}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={vi.fn()}
      />,
    )
    expect(screen.queryByLabelText('Vượt trần thao tác hàng loạt')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Chuyển tới' })).toBeEnabled()
  })

  it(`vượt trần ${MAX_BULK_FOLDER_IDS} thư mục → nút Chuyển tới cũng bị TẮT`, () => {
    const manyFolders = Array.from({ length: MAX_BULK_FOLDER_IDS + 1 }, (_, i) => i + 1)
    render(
      <FolderSelectionToolbar
        selectedFolderIds={manyFolders}
        selectedDocumentIds={[]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={vi.fn()}
      />,
    )
    expect(screen.getByLabelText('Vượt trần thao tác hàng loạt')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Chuyển tới' })).toBeDisabled()
  })
})

describe('FolderSelectionToolbar — nút «Xóa» (phản hồi lead 24/09/2026)', () => {
  it('chỉ chọn THƯ MỤC: «Xóa» hiện dù KHÔNG có quyền document.delete (folder tự thử được)', () => {
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[9]}
        selectedDocumentIds={[]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={vi.fn()}
      />,
    )
    expect(screen.getByRole('button', { name: 'Xóa' })).toBeInTheDocument()
  })

  it('chỉ chọn VĂN BẢN, thiếu document.delete → «Xóa» ẨN HẲN, không phải khóa', () => {
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[]}
        selectedDocumentIds={[1, 2]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={vi.fn()}
      />,
    )
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
  })

  it('chỉ chọn VĂN BẢN, ĐỦ document.delete → «Xóa» hiện, bấm gọi xóa từng văn bản rồi bỏ chọn', async () => {
    vi.mocked(usePermission).mockReturnValue({ can: () => true } as unknown as ReturnType<typeof usePermission>)
    const user = userEvent.setup()
    const onClear = vi.fn()
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[]}
        selectedDocumentIds={[1, 2]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={onClear}
        onShowDetails={vi.fn()}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'Xóa' }))
    expect(deleteDocumentMutate).toHaveBeenCalledWith(1)
    expect(deleteDocumentMutate).toHaveBeenCalledWith(2)
    expect(onClear).toHaveBeenCalledOnce()
  })

  it('bấm «Xóa» rồi HỦY hộp xác nhận → không gọi mutate nào', async () => {
    vi.mocked(confirm).mockResolvedValue(false)
    const user = userEvent.setup()
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[9]}
        selectedDocumentIds={[]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={vi.fn()}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'Xóa' }))
    expect(deleteFolderMutate).not.toHaveBeenCalled()
  })

  it('lượt chọn LẪN cả hai, thiếu quyền xóa văn bản → chỉ xóa THƯ MỤC, bỏ qua văn bản', async () => {
    const user = userEvent.setup()
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[9]}
        selectedDocumentIds={[1]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={vi.fn()}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'Xóa' }))
    expect(deleteFolderMutate).toHaveBeenCalledWith(9)
    expect(deleteDocumentMutate).not.toHaveBeenCalled()
  })

  it('phím Delete kích hoạt xóa lượt chọn hiện tại', async () => {
    const user = userEvent.setup()
    render(
      <FolderSelectionToolbar
        selectedFolderIds={[9]}
        selectedDocumentIds={[]}
        currentFolder={CURRENT_FOLDER}
        onClearSelection={vi.fn()}
        onShowDetails={vi.fn()}
      />,
    )
    await user.keyboard('{Delete}')
    expect(deleteFolderMutate).toHaveBeenCalledWith(9)
  })

  it('đang gõ trong Ô NHẬP thì phím Delete KHÔNG kích hoạt xóa lượt chọn', async () => {
    const user = userEvent.setup()
    render(
      <>
        <input aria-label="ô gõ ở nơi khác" />
        <FolderSelectionToolbar
          selectedFolderIds={[9]}
          selectedDocumentIds={[]}
          currentFolder={CURRENT_FOLDER}
          onClearSelection={vi.fn()}
          onShowDetails={vi.fn()}
        />
      </>,
    )
    await user.click(screen.getByLabelText('ô gõ ở nơi khác'))
    await user.keyboard('{Delete}')
    expect(deleteFolderMutate).not.toHaveBeenCalled()
  })
})
