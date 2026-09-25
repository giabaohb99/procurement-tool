import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  useCreateDocFolder,
  useDeleteDocFolder,
  useDocFolder,
  useDocFolderTree,
  useLinkDocumentsToFolder,
  useMoveDocFolder,
  useUnlinkDocumentsFromFolder,
  useUpdateDocFolder,
} from '../hooks/use-document-folders'
import { FOLDER_VIEW_STORAGE_KEY } from '../helpers/folder-view-storage-key'
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND, FOLDER_STATUS } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'
import { FolderMyDrivePanel } from './folder-my-drive-panel'

vi.mock('sonner', () => ({ toast: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }))
vi.mock('../hooks/use-document-folders', () => ({
  useDocFolderTree: vi.fn(),
  useDocFolder: vi.fn(() => ({ data: undefined })),
  useCreateDocFolder: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  useUpdateDocFolder: vi.fn(() => ({ mutate: vi.fn() })),
  useDeleteDocFolder: vi.fn(() => ({ mutate: vi.fn() })),
  useMoveDocFolder: vi.fn(() => ({ mutate: vi.fn() })),
  useLinkDocumentsToFolder: vi.fn(() => ({ mutate: vi.fn() })),
  useUnlinkDocumentsFromFolder: vi.fn(() => ({ mutate: vi.fn() })),
}))

function companyRoot(overrides: Partial<DocFolderTreeNode> & { id: number; name: string }): DocFolderTreeNode {
  return {
    company_id: overrides.id,
    parent_id: 0,
    kind: FOLDER_KIND.company,
    kind_label: 'Thư mục pháp nhân',
    code: '',
    path: `/${overrides.id}/`,
    depth: 0,
    sort_order: 0,
    status: FOLDER_STATUS.active,
    status_label: 'Đang dùng',
    document_count: 0,
    document_count_branch: 0,
    my_level: FOLDER_ACCESS_LEVEL.manage,
    ...overrides,
  }
}

const CTY_A = companyRoot({ id: 1, name: 'CÔNG TY A' })
const CTY_B = companyRoot({ id: 2, name: 'CÔNG TY B', document_count_branch: 12 })

beforeEach(() => {
  localStorage.clear()
  vi.mocked(useDocFolderTree).mockReturnValue({
    data: [CTY_A, CTY_B],
    isLoading: false,
    isFetching: false,
    refetch: vi.fn(),
  } as unknown as ReturnType<typeof useDocFolderTree>)
  vi.mocked(useDocFolder).mockReturnValue({ data: undefined } as unknown as ReturnType<typeof useDocFolder>)
  vi.mocked(useCreateDocFolder).mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof useCreateDocFolder>)
  vi.mocked(useUpdateDocFolder).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<typeof useUpdateDocFolder>)
  vi.mocked(useDeleteDocFolder).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<typeof useDeleteDocFolder>)
  vi.mocked(useMoveDocFolder).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<typeof useMoveDocFolder>)
  vi.mocked(useLinkDocumentsToFolder).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<
    typeof useLinkDocumentsToFolder
  >)
  vi.mocked(useUnlinkDocumentsFromFolder).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<
    typeof useUnlinkDocumentsFromFolder
  >)
})

describe('FolderMyDrivePanel — rỗng', () => {
  it('không thấy thư mục pháp nhân nào → báo rõ, không tự nổ', () => {
    vi.mocked(useDocFolderTree).mockReturnValue({
      data: [],
      isLoading: false,
      isFetching: false,
      refetch: vi.fn(),
    } as unknown as ReturnType<typeof useDocFolderTree>)
    render(<FolderMyDrivePanel onSelectFolder={vi.fn()} />)
    expect(
      screen.getByText('Bạn chưa thấy thư mục pháp nhân nào — liên hệ quản trị để được cấp quyền.'),
    ).toBeInTheDocument()
  })
})

describe('FolderMyDrivePanel — chế độ DANH SÁCH mặc định, dùng LẠI FolderListView', () => {
  it('mặc định là DANH SÁCH (chưa từng bấm) — hai pháp nhân hiện thành hai dòng', () => {
    render(<FolderMyDrivePanel onSelectFolder={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Xem dạng danh sách' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'CÔNG TY A' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'CÔNG TY B' })).toBeInTheDocument()
  })

  it('KHÔNG còn chữ "văn bản" nào trên dòng — khác bản cũ từng ghi "n văn bản"', () => {
    render(<FolderMyDrivePanel onSelectFolder={vi.fn()} />)
    expect(screen.queryByText(/văn bản/)).not.toBeInTheDocument()
  })

  //  Chốt 24/09/2026: bấm MỘT LẦN là MỞ (bỏ bấm đúp), chọn phải kèm phím.
  it('plain click on a row opens that company folder', async () => {
    const user = userEvent.setup()
    const onSelectFolder = vi.fn()
    render(<FolderMyDrivePanel onSelectFolder={onSelectFolder} />)
    await user.click(screen.getByRole('button', { name: 'CÔNG TY B' }))
    expect(onSelectFolder).toHaveBeenCalledTimes(1)
    expect(onSelectFolder).toHaveBeenCalledWith(2)
  })

  it('Ctrl+click only selects the row, does not open it', async () => {
    const user = userEvent.setup()
    const onSelectFolder = vi.fn()
    render(<FolderMyDrivePanel onSelectFolder={onSelectFolder} />)
    await user.keyboard('{Control>}')
    await user.click(screen.getByRole('button', { name: 'CÔNG TY A' }))
    await user.keyboard('{/Control}')
    expect(onSelectFolder).not.toHaveBeenCalled()
    expect(screen.getByRole('button', { name: 'CÔNG TY A' })).toHaveAttribute('data-selected', 'true')
  })
})

describe('FolderMyDrivePanel — chuyển sang chế độ LƯỚI, dùng LẠI FolderChildCards', () => {
  it('bấm «Xem dạng lưới» → đổi ngay sang thẻ pill, GHI vào ĐÚNG localStorage của một thư mục thật', async () => {
    const user = userEvent.setup()
    render(<FolderMyDrivePanel onSelectFolder={vi.fn()} />)
    await user.click(screen.getByRole('button', { name: 'Xem dạng lưới' }))

    expect(screen.getByRole('button', { name: 'Xem dạng lưới' })).toHaveAttribute('aria-pressed', 'true')
    expect(localStorage.getItem(FOLDER_VIEW_STORAGE_KEY)).toBe('1')
    //  Thẻ thư mục kiểu Drive (chốt 24/09/2026): tên hỗ trợ = đúng TÊN, dòng
    //  đếm là phần MÔ TẢ — rỗng thì ghi «Trống», có văn bản thì ghi số.
    expect(screen.getByRole('button', { name: 'CÔNG TY A' })).toHaveAccessibleDescription('Trống')
    expect(screen.getByRole('button', { name: 'CÔNG TY B' })).toHaveAccessibleDescription('12 văn bản')
  })

  it(`đã lưu chế độ LƯỚI từ MÀN THƯ MỤC THẬT (khóa ${FOLDER_VIEW_STORAGE_KEY}) → mở lại gốc vẫn ở Lưới`, () => {
    localStorage.setItem(FOLDER_VIEW_STORAGE_KEY, '1')
    render(<FolderMyDrivePanel onSelectFolder={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Xem dạng lưới' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('plain click on a pill card opens that company folder', async () => {
    localStorage.setItem(FOLDER_VIEW_STORAGE_KEY, '1')
    const user = userEvent.setup()
    const onSelectFolder = vi.fn()
    render(<FolderMyDrivePanel onSelectFolder={onSelectFolder} />)
    await user.click(screen.getByRole('button', { name: 'CÔNG TY A' }))
    expect(onSelectFolder).toHaveBeenCalledWith(1)
  })
})

describe('FolderMyDrivePanel — khung chi tiết bật/tắt được, menu ⋯ có mặt', () => {
  it('bấm nút khung chi tiết → mở khung, chưa chọn gì thì mời chọn', async () => {
    const user = userEvent.setup()
    render(<FolderMyDrivePanel onSelectFolder={vi.fn()} />)
    await user.click(screen.getByRole('button', { name: 'Bật/tắt khung chi tiết' }))
    expect(screen.getByText('Chọn một thư mục hoặc văn bản để xem chi tiết.')).toBeInTheDocument()
  })

  it('menu «⋯» của một dòng pháp nhân có mục «Xem chi tiết» (dùng chung FolderItemContextMenu)', async () => {
    const user = userEvent.setup()
    render(<FolderMyDrivePanel onSelectFolder={vi.fn()} />)
    const row = screen.getByRole('button', { name: 'CÔNG TY A' })
    await user.click(within(row.parentElement as HTMLElement).getByRole('button', { name: 'Thêm tùy chọn' }))
    expect(await screen.findByRole('menuitem', { name: 'Xem chi tiết' })).toBeInTheDocument()
  })
})
