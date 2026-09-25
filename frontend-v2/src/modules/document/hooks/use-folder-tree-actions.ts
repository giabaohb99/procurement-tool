import { useRef, useState } from 'react'

import {
  useArchiveDocFolder,
  useCreateDocFolder,
  useMoveDocFolder,
  useUpdateDocFolder,
} from './use-document-folders'
import { ROOT_PARENT_ID } from '../helpers/insert-temp-tree-node'
import { FOLDER_STATUS } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'
import type { FolderNodeAction } from '../components/folder-tree-actions-menu'

/**
 * State + mutation cho MỌI thao tác của menu `⋯`/chuột phải trên một nút cây
 * (`folder-tree-panel.tsx`) — tách khỏi component vẽ để tệp đó không vượt quá
 * 200 dòng (đổi tên tại chỗ, tạo thư mục kiểu VS Code «New Folder», chuyển,
 * ngừng dùng/khôi phục, xóa đều cần state hoặc mutation RIÊNG).
 *
 * ⚠️ Tạo thư mục KHÔNG còn mở hộp thoại (duoc-CR-476, yêu cầu 23/09/2026) — dòng
 * nhập xuất hiện NGAY TRONG cây (`insertTempChildNode`, `folder-tree-panel.tsx`).
 * Ô mã/mô tả của `folder-form-dialog.tsx` không còn đường vào từ đây nữa.
 */
export function useFolderTreeActions() {
  const [renamingId, setRenamingId] = useState<number | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [creatingUnder, setCreatingUnder] = useState<{
    parentId: number
    parentName: string
  } | null>(null)
  const [newFolderValue, setNewFolderValue] = useState('')
  const [moveTarget, setMoveTarget] = useState<DocFolderTreeNode | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<DocFolderTreeNode | null>(null)

  const updateFolder = useUpdateDocFolder()
  const archiveFolder = useArchiveDocFolder()
  const moveFolder = useMoveDocFolder()
  const createFolder = useCreateDocFolder()
  //  Chặn bấm đúp / Enter-rồi-blur-cùng-lúc (bẫy CR-317): `mutation.isPending`
  //  chỉ đúng ở lượt render SAU, không kịp chặn lượt gọi thứ hai trong cùng tick.
  const creatingRef = useRef(false)

  function startRename(node: DocFolderTreeNode) {
    setRenamingId(node.id)
    //  Thư mục pháp nhân chưa đặt tên tay có `name = ""` — mở ô với tên đang
    //  HIỂN THỊ để người dùng sửa tiếp, không phải gõ lại từ đầu.
    setRenameValue(node.name || node.display_name || '')
  }

  /** Gõ xong bấm Enter/rời ô — tên rỗng hoặc không đổi thì bỏ qua, không gọi API vô ích. */
  function commitRename(currentName: string | undefined) {
    if (renamingId == null) return
    const trimmed = renameValue.trim()
    if (trimmed && currentName != null && trimmed !== currentName) {
      updateFolder.mutate({ id: renamingId, payload: { name: trimmed } })
    }
    setRenamingId(null)
  }

  function startCreate(node: DocFolderTreeNode) {
    setCreatingUnder({ parentId: node.id, parentName: node.name })
    setNewFolderValue('')
  }

  /** Dòng «thư mục mới» ở GỐC cây — thư mục tự do, backend cho người tạo mức Quản lý. */
  function startCreateAtRoot() {
    setCreatingUnder({ parentId: ROOT_PARENT_ID, parentName: '' })
    setNewFolderValue('')
  }

  function cancelCreate() {
    setCreatingUnder(null)
    setNewFolderValue('')
  }

  /** Enter/rời ô của dòng «thư mục mới» — tên rỗng thì HỦY (không tạo bản ghi rỗng). */
  function commitCreate(onCreated: (folder: DocFolderTreeNode) => void) {
    if (!creatingUnder || creatingRef.current) return
    const trimmed = newFolderValue.trim()
    if (!trimmed) {
      cancelCreate()
      return
    }
    creatingRef.current = true
    createFolder.mutate(
      { parent_id: creatingUnder.parentId, name: trimmed },
      {
        onSuccess: (folder) => {
          creatingRef.current = false
          cancelCreate()
          onCreated(folder)
        },
        onError: () => {
          //  Giữ nguyên dòng tạm + tên đã gõ để người dùng sửa lại và thử tiếp
          //  (lỗi trùng tên, hết quyền…) — API tự toast lý do.
          creatingRef.current = false
        },
      },
    )
  }

  function handleAction(
    node: DocFolderTreeNode,
    action: FolderNodeAction,
    onAccess: (id: number) => void,
  ) {
    switch (action) {
      case 'add-child':
        startCreate(node)
        break
      case 'rename':
        startRename(node)
        break
      case 'move':
        setMoveTarget(node)
        break
      case 'access':
        onAccess(node.id)
        break
      case 'archive':
        archiveFolder.mutate(node.id)
        break
      case 'restore':
        updateFolder.mutate({ id: node.id, payload: { status: FOLDER_STATUS.active } })
        break
      case 'delete':
        setDeleteTarget(node)
        break
    }
  }

  return {
    renamingId,
    renameValue,
    setRenameValue,
    startRename,
    commitRename,
    cancelRename: () => setRenamingId(null),
    creatingUnder,
    newFolderValue,
    setNewFolderValue,
    startCreate,
    startCreateAtRoot,
    commitCreate,
    cancelCreate,
    creating: createFolder.isPending,
    moveTarget,
    setMoveTarget,
    deleteTarget,
    setDeleteTarget,
    handleAction,
    moveFolder,
  }
}
