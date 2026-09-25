import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { TreeNode } from '@/shared/tree/tree-types'
import { FOLDER_DRAG_MIME, writeFolderDragPayload } from '../helpers/folder-drag-payload'
import { NEW_FOLDER_TEMP_ID } from '../helpers/insert-temp-tree-node'
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND, FOLDER_STATUS } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'
import { useFolderDragMove } from './use-folder-drag-move'

vi.mock('sonner', () => ({ toast: { success: vi.fn(), warning: vi.fn(), error: vi.fn() } }))
vi.mock('../api/document-folder-api', () => ({
  documentFolderApi: {
    linkDocuments: vi.fn().mockResolvedValue({ moved: [], denied: [] }),
    unlinkDocuments: vi.fn().mockResolvedValue({ moved: [], denied: [] }),
    move: vi.fn().mockResolvedValue({}),
    reorder: vi.fn().mockResolvedValue({ changed: 0 }),
  },
}))

function folderRow(overrides: Partial<DocFolderTreeNode>): DocFolderTreeNode {
  return {
    id: 10,
    company_id: 1,
    parent_id: 0,
    kind: FOLDER_KIND.normal,
    kind_label: 'Thư mục',
    name: 'Đích',
    code: '',
    path: '/10/',
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

function targetNode(id: number): TreeNode<DocFolderTreeNode> {
  return { id, label: 'Đích', data: folderRow({ id }) }
}

/** Sự kiện `DragEvent` giả tối thiểu — chỉ cần đủ field `onExternalDropNode` đọc tới. */
function makeDropEvent(
  payload: { documentIds: number[]; folderIds: number[]; sourceFolderId: number | null },
  altKey = false,
) {
  const dataTransfer = {
    setData: vi.fn(),
    getData: vi.fn(),
    types: [FOLDER_DRAG_MIME],
  } as unknown as DataTransfer
  writeFolderDragPayload(dataTransfer, payload)
  // `writeFolderDragPayload` gọi `setData` (mock) — đọc lại đúng chuỗi vừa ghi để `getData` trả đúng giá trị.
  const written = (dataTransfer.setData as ReturnType<typeof vi.fn>).mock.calls[0]?.[1] as string
  ;(dataTransfer.getData as ReturnType<typeof vi.fn>).mockReturnValue(written)
  return { dataTransfer, altKey } as unknown as React.DragEvent<HTMLDivElement>
}

let queryClient: QueryClient
function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

beforeEach(() => {
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  //  `restoreMocks` của `vitest.config.ts` chỉ khôi phục mock tạo bằng
  //  `vi.spyOn` — các `vi.fn()` khai trong factory `vi.mock(...)` ở đầu tệp
  //  KHÔNG tự dọn lịch sử gọi giữa các bài kiểm, phải tự xóa ở đây.
  vi.clearAllMocks()
})

describe('useFolderDragMove — nhận payload ngoài cây (kéo từ khung phải)', () => {
  //  Đổi 24/09/2026 (lỗi đại ca báo: kéo văn bản sang thư mục khác mà nó vẫn
  //  nằm ở chỗ cũ, nhìn như "tạo thêm một file"): mặc định CHUYỂN, giữ Alt mới
  //  là THÊM một chỗ nữa — ngược với luật cũ.
  it('dropping a document MOVES it by default: link to target, then unlink from source', async () => {
    const { result } = renderHook(() => useFolderDragMove([folderRow({ id: 10 })]), { wrapper })
    const { documentFolderApi } = await import('../api/document-folder-api')

    result.current.onExternalDropNode(
      targetNode(10),
      makeDropEvent({ documentIds: [1, 2], folderIds: [], sourceFolderId: 5 }),
    )

    await waitFor(() =>
      expect(documentFolderApi.linkDocuments).toHaveBeenCalledWith({
        document_ids: [1, 2],
        folder_id: 10,
        mode: 'add',
      }),
    )
    await waitFor(() =>
      expect(documentFolderApi.unlinkDocuments).toHaveBeenCalledWith({
        document_ids: [1, 2],
        folder_id: 5,
      }),
    )
  })

  it('holding Alt only ADDS the document to the target and keeps it in the source', async () => {
    const { result } = renderHook(() => useFolderDragMove([folderRow({ id: 10 })]), { wrapper })
    const { documentFolderApi } = await import('../api/document-folder-api')

    result.current.onExternalDropNode(
      targetNode(10),
      makeDropEvent({ documentIds: [1], folderIds: [], sourceFolderId: 5 }, true),
    )

    await waitFor(() => expect(documentFolderApi.linkDocuments).toHaveBeenCalled())
    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(documentFolderApi.unlinkDocuments).not.toHaveBeenCalled()
  })

  it('sourceFolderId null thì KHÔNG gọi unlinkDocuments (không có nguồn để gỡ)', async () => {
    const { result } = renderHook(() => useFolderDragMove([folderRow({ id: 10 })]), { wrapper })
    const { documentFolderApi } = await import('../api/document-folder-api')

    result.current.onExternalDropNode(
      targetNode(10),
      makeDropEvent({ documentIds: [1], folderIds: [], sourceFolderId: null }),
    )

    await waitFor(() => expect(documentFolderApi.linkDocuments).toHaveBeenCalled())
    expect(documentFolderApi.unlinkDocuments).not.toHaveBeenCalled()
  })

  it('thả thư mục gọi move với newParentId đúng đích, bỏ qua chính nó nếu trùng', async () => {
    const { result } = renderHook(() => useFolderDragMove([folderRow({ id: 10 })]), { wrapper })
    const { documentFolderApi } = await import('../api/document-folder-api')

    result.current.onExternalDropNode(
      targetNode(10),
      makeDropEvent({ documentIds: [], folderIds: [7, 10], sourceFolderId: null }),
    )

    await waitFor(() => expect(documentFolderApi.move).toHaveBeenCalledWith(7, 10))
    expect(documentFolderApi.move).toHaveBeenCalledTimes(1)
  })

  it('payload rỗng cả hai mảng thì không gọi mutation nào (không nổ)', async () => {
    const { result } = renderHook(() => useFolderDragMove([folderRow({ id: 10 })]), { wrapper })
    const { documentFolderApi } = await import('../api/document-folder-api')

    result.current.onExternalDropNode(
      targetNode(10),
      makeDropEvent({ documentIds: [], folderIds: [], sourceFolderId: null }),
    )

    expect(documentFolderApi.linkDocuments).not.toHaveBeenCalled()
    expect(documentFolderApi.move).not.toHaveBeenCalled()
  })

  it('acceptsExternalDrop từ chối dòng tạm "thư mục mới" và node không có data thật', () => {
    const { result } = renderHook(() => useFolderDragMove([folderRow({ id: 10 })]), { wrapper })
    expect(result.current.acceptsExternalDrop({ id: NEW_FOLDER_TEMP_ID, label: '' })).toBe(false)
    expect(result.current.acceptsExternalDrop(targetNode(10))).toBe(true)
  })
})

//  Lỗi báo 24/09/2026: kéo thư mục con ra GỐC cây không có chỗ nào để thả.
//  Nhãn «THƯ MỤC» ở đầu cây nay là đích thả — xem `canDropOnRoot`/`dropOnRoot`.
describe('useFolderDragMove — thả ra GỐC cây', () => {
  const PARENT = folderRow({ id: 1, name: 'Cha', path: '/1/', depth: 1 })
  const CHILD = folderRow({ id: 5, parent_id: 1, name: 'Con', path: '/1/5/', depth: 2 })
  const ROOT_FOLDER = folderRow({ id: 9, parent_id: 0, name: 'Gốc sẵn', path: '/9/', depth: 1 })
  const noPayloadEvent = {
    dataTransfer: { types: [], getData: vi.fn(() => '') },
  } as unknown as React.DragEvent<HTMLElement>

  it('a subfolder dragged INSIDE the tree can be dropped on root and moves to parent 0', async () => {
    const { result } = renderHook(() => useFolderDragMove([PARENT, CHILD]), { wrapper })
    const { documentFolderApi } = await import('../api/document-folder-api')
    act(() => result.current.onDragStartNode({ id: 5, label: 'Con', data: CHILD }))
    expect(result.current.canDropOnRoot(noPayloadEvent)).toBe(true)
    act(() => result.current.dropOnRoot(noPayloadEvent))
    await waitFor(() => expect(documentFolderApi.move).toHaveBeenCalledWith(5, 0))
  })

  it('a folder already at root cannot be dropped on root (nothing would change)', () => {
    const { result } = renderHook(() => useFolderDragMove([ROOT_FOLDER]), { wrapper })
    act(() => result.current.onDragStartNode({ id: 9, label: 'Gốc sẵn', data: ROOT_FOLDER }))
    expect(result.current.canDropOnRoot(noPayloadEvent)).toBe(false)
  })

  it('a folder dragged from the RIGHT panel (payload) also moves to root', async () => {
    const { result } = renderHook(() => useFolderDragMove([PARENT, CHILD]), { wrapper })
    const { documentFolderApi } = await import('../api/document-folder-api')
    const event = makeDropEvent({ documentIds: [], folderIds: [5], sourceFolderId: 1 })
    expect(result.current.canDropOnRoot(event)).toBe(true)
    act(() => result.current.dropOnRoot(event))
    await waitFor(() => expect(documentFolderApi.move).toHaveBeenCalledWith(5, 0))
  })

  it('nothing being dragged → root is not a drop target', () => {
    const { result } = renderHook(() => useFolderDragMove([PARENT, CHILD]), { wrapper })
    expect(result.current.canDropOnRoot(noPayloadEvent)).toBe(false)
  })

  it('a branch holding documents asks for confirmation first instead of moving straight away', async () => {
    const withDocs = { ...CHILD, document_count_branch: 3 }
    const { result } = renderHook(() => useFolderDragMove([PARENT, withDocs]), { wrapper })
    const { documentFolderApi } = await import('../api/document-folder-api')
    act(() => result.current.onDragStartNode({ id: 5, label: 'Con', data: withDocs }))
    act(() => result.current.dropOnRoot(noPayloadEvent))
    expect(result.current.pendingDrop).toEqual({ source: withDocs, targetId: 0 })
    expect(documentFolderApi.move).not.toHaveBeenCalled()
  })
})
