import { renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useFolderDropActions } from './use-folder-drop-actions'
import { FOLDER_LINK_MODE } from '../types/document-folder'

const link = vi.fn()
const unlink = vi.fn()
const moveFolder = vi.fn()

vi.mock('./use-document-folders', () => ({
  useLinkDocumentsToFolder: () => ({ mutate: link }),
  useUnlinkDocumentsFromFolder: () => ({ mutate: unlink }),
  useMoveDocFolder: () => ({ mutate: moveFolder }),
}))
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: vi.fn() }))

/** Giả lập API gắn văn bản thành công — gọi ngay `onSuccess` như TanStack Query. */
function linkSucceeds() {
  link.mockImplementation((_vars: unknown, opts?: { onSuccess?: () => void }) =>
    opts?.onSuccess?.(),
  )
}

describe('useFolderDropActions.handleDropOnFolder', () => {
  beforeEach(() => {
    link.mockReset()
    unlink.mockReset()
    moveFolder.mockReset()
  })

  //  Lỗi báo 24/09/2026: kéo văn bản sang thư mục khác mà nó vẫn nằm ở thư mục
  //  cũ — người dùng thấy như bị "tạo thêm một file". Mặc định phải CHUYỂN.
  it('moves documents by default: links to target, then unlinks ONLY from the source folder', () => {
    linkSucceeds()
    const { result } = renderHook(() => useFolderDropActions(5, 'Nguồn'))
    result.current.handleDropOnFolder(
      9,
      { documentIds: [1, 2], folderIds: [], sourceFolderId: 5 },
      false,
    )
    expect(link).toHaveBeenCalledWith(
      { document_ids: [1, 2], folder_id: 9, mode: FOLDER_LINK_MODE.add },
      expect.anything(),
    )
    expect(unlink).toHaveBeenCalledWith({ document_ids: [1, 2], folder_id: 5 })
  })

  it('never uses replace mode — that would strip the document from every OTHER folder too', () => {
    linkSucceeds()
    const { result } = renderHook(() => useFolderDropActions(5, 'Nguồn'))
    result.current.handleDropOnFolder(
      9,
      { documentIds: [1], folderIds: [], sourceFolderId: 5 },
      false,
    )
    expect(link.mock.calls[0][0].mode).not.toBe(FOLDER_LINK_MODE.replace)
  })

  it('holding Alt keeps the document in the source folder too (adds a second place)', () => {
    linkSucceeds()
    const { result } = renderHook(() => useFolderDropActions(5, 'Nguồn'))
    result.current.handleDropOnFolder(
      9,
      { documentIds: [1], folderIds: [], sourceFolderId: 5 },
      true,
    )
    expect(link).toHaveBeenCalledTimes(1)
    expect(unlink).not.toHaveBeenCalled()
  })

  it('does not unlink when linking fails — the document must never end up in no folder', () => {
    link.mockImplementation(() => undefined)
    const { result } = renderHook(() => useFolderDropActions(5, 'Nguồn'))
    result.current.handleDropOnFolder(
      9,
      { documentIds: [1], folderIds: [], sourceFolderId: 5 },
      false,
    )
    expect(unlink).not.toHaveBeenCalled()
  })

  it('dropping onto the same folder it came from does not unlink it', () => {
    linkSucceeds()
    const { result } = renderHook(() => useFolderDropActions(5, 'Nguồn'))
    result.current.handleDropOnFolder(
      5,
      { documentIds: [1], folderIds: [], sourceFolderId: 5 },
      false,
    )
    expect(unlink).not.toHaveBeenCalled()
  })

  it('no known source (dragged from the root view) → just links, nothing to unlink', () => {
    linkSucceeds()
    const { result } = renderHook(() => useFolderDropActions(5, 'Nguồn'))
    result.current.handleDropOnFolder(
      9,
      { documentIds: [1], folderIds: [], sourceFolderId: null },
      false,
    )
    expect(unlink).not.toHaveBeenCalled()
  })

  it('folders are moved (re-parented) and never linked', () => {
    const { result } = renderHook(() => useFolderDropActions(5, 'Nguồn'))
    result.current.handleDropOnFolder(
      9,
      { documentIds: [], folderIds: [7, 9], sourceFolderId: 5 },
      false,
    )
    expect(moveFolder).toHaveBeenCalledTimes(1)
    expect(moveFolder).toHaveBeenCalledWith({ id: 7, newParentId: 9 })
    expect(link).not.toHaveBeenCalled()
  })
})
