import { useState } from 'react'

import type { DocFolderTreeNode } from '../types/document-folder'

/**
 * State + hành động của MỘT dòng thư mục con trong khung nội dung — đổi tên ·
 * chuyển tới… · chia sẻ · xóa. Tách khỏi `folder-child-cards.tsx` (nơi trước
 * đây giữ RIÊNG bốn `useState` này) để dùng LẠI y nguyên cho
 * `folder-list-view.tsx` (phase 10, duoc-CR-476) — hai nơi hiện cùng một thư
 * mục con dưới hai lớp vỏ khác nhau (thẻ pill kiểu Lưới / dòng kiểu Danh
 * sách) nhưng cùng một tập hành động, chép state hai lần là chỗ dễ trôi khi
 * có ai sửa một bên rồi quên bên kia.
 */
export function useFolderRowActions() {
  const [renameTarget, setRenameTarget] = useState<DocFolderTreeNode | null>(null)
  const [moveTarget, setMoveTarget] = useState<DocFolderTreeNode | null>(null)
  const [shareTargetId, setShareTargetId] = useState<number | null>(null)
  //  Thư mục đang mở hộp xóa (`FolderDeleteDialog`) — hộp đếm văn bản và bắt
  //  chọn nơi lưu mới cho văn bản sẽ mồ côi, không còn là một câu confirm trơn.
  const [deleteTarget, setDeleteTarget] = useState<DocFolderTreeNode | null>(null)

  function requestDelete(folder: DocFolderTreeNode) {
    setDeleteTarget(folder)
  }

  return {
    renameTarget,
    setRenameTarget,
    moveTarget,
    setMoveTarget,
    shareTargetId,
    setShareTargetId,
    requestDelete,
    deleteTarget,
    setDeleteTarget,
  }
}
