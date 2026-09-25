import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { FOLDER_ACCESS_LEVEL, type DocFolderTreeNode, type FolderDeletePreview } from '../types/document-folder'
import { FolderDeleteDialog } from './folder-delete-dialog'

const { mutate, state } = vi.hoisted(() => ({
  mutate: vi.fn(),
  state: {
    preview: undefined as FolderDeletePreview | undefined,
    tree: [] as Array<{ id: number; my_level: number }>,
  },
}))

vi.mock('../hooks/use-document-folders', () => ({
  useFolderDeletePreview: () => ({ data: state.preview, isLoading: false }),
  useDocFolderTree: () => ({ data: state.tree }),
  useDeleteDocFolder: () => ({ mutate, isPending: false }),
}))
//  Ô chọn thư mục thật có test riêng — ở đây chỉ cần "người dùng chọn thư mục 77"
//  và "người dùng chọn chính thư mục đang xóa (5)".
vi.mock('./folder-picker', () => ({
  FolderPicker: ({ onChange }: { onChange: (ids: number[]) => void }) => (
    <>
      <button type="button" onClick={() => onChange([77])}>
        chọn thư mục 77
      </button>
      <button type="button" onClick={() => onChange([5])}>
        chọn chính nó
      </button>
    </>
  ),
}))

const FOLDER = { id: 5, name: 'Nhân sự', display_name: 'Nhân sự' } as DocFolderTreeNode

function preview(over: Partial<FolderDeletePreview>): FolderDeletePreview {
  return { blocked_reason: '', document_count: 0, orphan_count: 0, parent_id: 21, ...over }
}

function deleteButton() {
  return screen.getByRole('button', { name: /xóa$/i })
}

describe('FolderDeleteDialog', () => {
  beforeEach(() => {
    mutate.mockReset()
    state.tree = [{ id: 21, my_level: FOLDER_ACCESS_LEVEL.contribute }]
  })

  it('empty folder deletes without asking for a destination', () => {
    state.preview = preview({})
    render(<FolderDeleteDialog folder={FOLDER} onClose={vi.fn()} />)
    fireEvent.click(deleteButton())
    expect(mutate).toHaveBeenCalledWith({ id: 5, moveTo: undefined }, expect.anything())
  })

  it('orphaned documents go to the parent folder by default when the user may add documents there', () => {
    state.preview = preview({ document_count: 3, orphan_count: 2 })
    render(<FolderDeleteDialog folder={FOLDER} onClose={vi.fn()} />)
    expect(screen.getByText(/2 văn bản chỉ nằm trong thư mục này sẽ chuyển sang đây/)).toBeInTheDocument()
    expect(screen.getByText(/1 văn bản còn nằm ở thư mục khác/)).toBeInTheDocument()
    fireEvent.click(deleteButton())
    expect(mutate).toHaveBeenCalledWith({ id: 5, moveTo: 21 }, expect.anything())
  })

  it('does not suggest a parent the user cannot add documents to — delete stays locked until a folder is picked', () => {
    state.tree = [{ id: 21, my_level: FOLDER_ACCESS_LEVEL.view }]
    state.preview = preview({ document_count: 1, orphan_count: 1 })
    render(<FolderDeleteDialog folder={FOLDER} onClose={vi.fn()} />)
    expect(deleteButton()).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'chọn thư mục 77' }))
    fireEvent.click(deleteButton())
    expect(mutate).toHaveBeenCalledWith({ id: 5, moveTo: 77 }, expect.anything())
  })

  it('refuses the folder being deleted as the destination', () => {
    state.preview = preview({ document_count: 1, orphan_count: 1 })
    render(<FolderDeleteDialog folder={FOLDER} onClose={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: 'chọn chính nó' }))
    expect(screen.getByText(/Không chuyển vào chính thư mục đang xóa/)).toBeInTheDocument()
    expect(deleteButton()).toBeDisabled()
  })

  it('documents that live elsewhere too never get a destination — nothing is orphaned', () => {
    state.preview = preview({ document_count: 2, orphan_count: 0 })
    render(<FolderDeleteDialog folder={FOLDER} onClose={vi.fn()} />)
    expect(screen.queryByText('Chuyển văn bản sang')).not.toBeInTheDocument()
    fireEvent.click(deleteButton())
    expect(mutate).toHaveBeenCalledWith({ id: 5, moveTo: undefined }, expect.anything())
  })

  it('shows why a folder cannot be deleted and keeps the button locked', () => {
    state.preview = preview({ blocked_reason: 'Thư mục còn thư mục con, không xóa được' })
    render(<FolderDeleteDialog folder={FOLDER} onClose={vi.fn()} />)
    expect(screen.getByText('Thư mục còn thư mục con, không xóa được')).toBeInTheDocument()
    expect(deleteButton()).toBeDisabled()
  })

  //  Bẫy thứ tư CR-317: bấm liền tay hai lần ra hai lượt xóa.
  it('a double click sends exactly one delete', () => {
    state.preview = preview({})
    render(<FolderDeleteDialog folder={FOLDER} onClose={vi.fn()} />)
    fireEvent.click(deleteButton())
    fireEvent.click(deleteButton())
    expect(mutate).toHaveBeenCalledTimes(1)
  })
})
