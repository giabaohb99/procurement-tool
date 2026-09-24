import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

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
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND, FOLDER_STATUS } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'
import { FolderTreePanelShell } from './folder-tree-panel-shell'

const ROOT: DocFolderTreeNode = {
  id: 1,
  company_id: 1,
  parent_id: 0,
  kind: FOLDER_KIND.company,
  kind_label: 'Thư mục pháp nhân',
  name: 'CÔNG TY',
  code: '',
  path: '/1/',
  depth: 0,
  sort_order: 0,
  status: FOLDER_STATUS.active,
  status_label: 'Đang dùng',
  document_count: 0,
  document_count_branch: 0,
  my_level: FOLDER_ACCESS_LEVEL.manage,
}

vi.mock('sonner', () => ({ toast: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }))
vi.mock('../hooks/use-folder-tree-document-leaves', () => ({
  useFolderTreeDocumentLeaves: () => new Map(),
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

function idleMutation() {
  return { mutate: vi.fn(), isPending: false, mutateAsync: vi.fn() }
}

const WIDTH_KEY = 'erp.document.folders.tree-width'
const COLLAPSED_KEY = 'erp.document.folders.tree-collapsed'

beforeEach(() => {
  localStorage.clear()
  vi.mocked(useDocFolderTree).mockReturnValue({
    data: [ROOT],
    isLoading: false,
    isFetching: false,
    refetch: vi.fn(),
  } as unknown as ReturnType<typeof useDocFolderTree>)
  vi.mocked(useCreateDocFolder).mockReturnValue(idleMutation() as unknown as ReturnType<typeof useCreateDocFolder>)
  vi.mocked(useUpdateDocFolder).mockReturnValue(idleMutation() as unknown as ReturnType<typeof useUpdateDocFolder>)
  vi.mocked(useArchiveDocFolder).mockReturnValue(idleMutation() as unknown as ReturnType<typeof useArchiveDocFolder>)
  vi.mocked(useDeleteDocFolder).mockReturnValue(idleMutation() as unknown as ReturnType<typeof useDeleteDocFolder>)
  vi.mocked(useMoveDocFolder).mockReturnValue(idleMutation() as unknown as ReturnType<typeof useMoveDocFolder>)
  vi.mocked(useReorderDocFolders).mockReturnValue(
    idleMutation() as unknown as ReturnType<typeof useReorderDocFolders>,
  )
  vi.mocked(useLinkDocumentsToFolder).mockReturnValue(
    idleMutation() as unknown as ReturnType<typeof useLinkDocumentsToFolder>,
  )
  vi.mocked(useUnlinkDocumentsFromFolder).mockReturnValue(
    idleMutation() as unknown as ReturnType<typeof useUnlinkDocumentsFromFolder>,
  )
})

function renderShell() {
  return render(
    <MemoryRouter>
      <FolderTreePanelShell
        selectedFolderId={null}
        onSelectFolder={vi.fn()}
        onSelectDocument={vi.fn()}
        onOpenAccessTab={vi.fn()}
      />
    </MemoryRouter>,
  )
}

describe('FolderTreePanelShell — bề rộng nhớ localStorage', () => {
  it('chưa có gì trong localStorage thì dựng tay kéo với bề rộng mặc định 288px', () => {
    renderShell()
    const handle = screen.getByRole('separator', { name: 'Kéo để đổi bề ngang khung thư mục' })
    expect(handle).toHaveAttribute('aria-valuenow', '288')
    expect(handle).toHaveAttribute('aria-valuemin', '200')
    expect(handle).toHaveAttribute('aria-valuemax', '480')
  })

  it('đã lưu bề rộng từ phiên trước thì đọc lại ĐÚNG số đó, không phải mặc định', () => {
    localStorage.setItem(WIDTH_KEY, '350')
    renderShell()
    expect(
      screen.getByRole('separator', { name: 'Kéo để đổi bề ngang khung thư mục' }),
    ).toHaveAttribute('aria-valuenow', '350')
  })
})

describe('FolderTreePanelShell — gập hẳn khung', () => {
  it('bấm "Thu gọn khung thư mục" thì ẩn cây, chỉ còn thanh hẹp có nút mở lại', async () => {
    const user = userEvent.setup()
    renderShell()
    await user.click(screen.getByRole('button', { name: 'Thu gọn khung thư mục' }))

    expect(screen.getByRole('button', { name: 'Mở lại khung thư mục' })).toBeInTheDocument()
    expect(screen.queryByRole('tree', { name: 'Cây thư mục văn bản' })).not.toBeInTheDocument()
  })

  it('trạng thái gập được NHỚ LẠI qua localStorage — dựng lại từ đầu vẫn thấy thanh hẹp', () => {
    localStorage.setItem(COLLAPSED_KEY, '1')
    renderShell()
    expect(screen.getByRole('button', { name: 'Mở lại khung thư mục' })).toBeInTheDocument()
  })

  it('bấm "Mở lại khung thư mục" thì hiện cây trở lại', async () => {
    localStorage.setItem(COLLAPSED_KEY, '1')
    const user = userEvent.setup()
    renderShell()
    await user.click(screen.getByRole('button', { name: 'Mở lại khung thư mục' }))
    expect(screen.getByRole('tree', { name: 'Cây thư mục văn bản' })).toBeInTheDocument()
  })
})
