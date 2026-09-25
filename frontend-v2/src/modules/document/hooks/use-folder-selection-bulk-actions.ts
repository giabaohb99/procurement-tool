import { useEffect } from 'react'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { confirm } from '@/shared/ui/confirm-dialog'
import { folderBulkResultMessage } from '../helpers/folder-bulk-result-message'
import { isEditableTarget } from './use-item-selection'
import {
  useDeleteDocFolder,
  useLinkDocumentsToFolder,
  useMoveDocFolder,
  useUnlinkDocumentsFromFolder,
} from './use-document-folders'
import { useDeleteDocument } from './use-documents'
import { FOLDER_LINK_MODE } from '../types/document-folder'

/**
 * Trần văn bản một lượt thao tác HÀNG LOẠT trên thư mục — khớp trần backend
 * của `folder_link_bulk_service` (rà soát code-reviewer 23/09/2026, M5).
 * Chặn TỪ PHÍA CLIENT trước khi gọi, không đợi 500 lỗi trả về mới báo.
 */
export const MAX_BULK_DOCUMENT_IDS = 500
/**
 * Trần THƯ MỤC một lượt — không có "API hàng loạt" cho thư mục (mỗi thư mục
 * một lệnh `move` riêng), nên trần ở đây là an toàn CLIENT tự đặt để tránh bắn
 * hàng trăm request tuần tự, không phải khớp một con số backend nào.
 */
export const MAX_BULK_FOLDER_IDS = 50

interface UseFolderSelectionBulkActionsArgs {
  selectedFolderIds: number[]
  selectedDocumentIds: number[]
  currentFolder: { id: number; name: string }
  onClearSelection: () => void
}

/**
 * MUTATION + trần + phím `Delete` của thanh thao tác hàng loạt kiểu Drive
 * (`folder-selection-toolbar.tsx`) — tách ra để tệp đó chỉ còn lo GIAO DIỆN
 * (nút icon + tooltip), dưới 200 dòng.
 *
 * Câu kết quả (thêm/chuyển/gỡ bao nhiêu, bị từ chối bao nhiêu) nay đi qua
 * `toast` (sonner) — cùng lối với mọi thao tác hàng loạt khác của module này
 * (`use-document-folder-access.ts`…) — thay vì một dòng chữ RIÊNG kẹt trong
 * chính thanh thao tác. Nhờ vậy thanh này chỉ còn MỘT trạng thái hiện/ẩn
 * (`total > 0`), khớp đúng luật "thay chỗ hàng lọc" (đặc tả duoc-CR-476,
 * phản hồi 24/09/2026): không còn ca "đã bỏ chọn nhưng thanh vẫn đứng đó" mà
 * `folder-documents-view.tsx` phải né riêng.
 */
export function useFolderSelectionBulkActions({
  selectedFolderIds,
  selectedDocumentIds,
  currentFolder,
  onClearSelection,
}: UseFolderSelectionBulkActionsArgs) {
  const link = useLinkDocumentsToFolder()
  const unlink = useUnlinkDocumentsFromFolder()
  const moveFolder = useMoveDocFolder()
  const deleteFolder = useDeleteDocFolder()
  const deleteDocument = useDeleteDocument()
  const { can } = usePermission()
  //  Xóa THƯ MỤC luôn thử được từ đây (backend tự chặn + báo lỗi rõ nếu còn
  //  con/văn bản — toast tự nổi qua `http-client.ts`, không cần đoán trước).
  //  Xóa VĂN BẢN cần `document.delete` — thiếu quyền thì bỏ hẳn phần văn bản
  //  ra khỏi lượt xóa (không phải khóa cả nút, tránh chặn luôn phần thư mục
  //  hợp lệ trong một lượt chọn LẪN cả hai loại).
  const canDeleteDocuments = can('document', 'delete')

  const total = selectedFolderIds.length + selectedDocumentIds.length
  const hasFolders = selectedFolderIds.length > 0
  const overDocCap = selectedDocumentIds.length > MAX_BULK_DOCUMENT_IDS
  const overFolderCap = selectedFolderIds.length > MAX_BULK_FOLDER_IDS
  const overCap = overDocCap || overFolderCap
  //  «Xóa» (phản hồi lead 24/09/2026, hạng mục §2) — hiện khi có THƯ MỤC trong
  //  lượt chọn (luôn thử được), hoặc có VĂN BẢN VÀ đủ quyền `document.delete`.
  const deletableDocumentCount = canDeleteDocuments ? selectedDocumentIds.length : 0
  const showDelete = hasFolders || deletableDocumentCount > 0

  async function runDelete() {
    if (!showDelete || overCap) return
    const skippedDocCount = selectedDocumentIds.length - deletableDocumentCount
    const ok = await confirm({
      title: `Xóa ${total} mục đã chọn?`,
      message:
        'Thư mục còn thư mục con sẽ không xóa được. Văn bản chỉ nằm trong thư mục bị ' +
        'xóa sẽ về thư mục pháp nhân của nó (muốn chọn nơi khác thì xóa từng thư mục). ' +
        'Văn bản xóa HẲN khỏi hệ thống — không phục hồi được.' +
        (skippedDocCount > 0
          ? ` ${skippedDocCount} văn bản không đủ quyền xóa sẽ được BỎ QUA.`
          : ''),
      confirmLabel: 'Xóa',
    })
    if (!ok) return
    for (const id of selectedFolderIds) deleteFolder.mutate(id)
    if (canDeleteDocuments) {
      for (const id of selectedDocumentIds) deleteDocument.mutate(id)
    }
    onClearSelection()
  }

  //  Phím `Delete` xóa NGUYÊN lượt chọn hiện tại (đặc tả §2, phản hồi lead
  //  24/09/2026) — gắn ở `window` cùng lối Esc/Ctrl+A của `useItemSelection`,
  //  chỉ chạy khi có gì XÓA ĐƯỢC và con trỏ KHÔNG đang gõ chữ.
  useEffect(() => {
    if (!showDelete) return
    function onKeyDown(event: KeyboardEvent) {
      if (isEditableTarget(event.target)) return
      if (event.key === 'Delete') {
        event.preventDefault()
        void runDelete()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `runDelete` đọc lại đúng state mới nhất mỗi lần gắn lại effect (phụ thuộc đã liệt kê đủ những gì thật sự đổi ý nghĩa của nó)
  }, [showDelete, selectedFolderIds, selectedDocumentIds, canDeleteDocuments, overCap])

  function runUnlink() {
    unlink.mutate(
      { document_ids: selectedDocumentIds, folder_id: currentFolder.id },
      {
        onSuccess: (result) => {
          toast.success(folderBulkResultMessage('gỡ', result))
          onClearSelection()
        },
      },
    )
  }

  function runAdd(targetFolderId: number) {
    link.mutate(
      { document_ids: selectedDocumentIds, folder_id: targetFolderId, mode: FOLDER_LINK_MODE.add },
      { onSuccess: (result) => toast.success(folderBulkResultMessage('thêm', result)) },
    )
    onClearSelection()
  }

  function runMoveTo(targetFolderId: number) {
    for (const folderId of selectedFolderIds) {
      moveFolder.mutate({ id: folderId, newParentId: targetFolderId })
    }
    if (selectedDocumentIds.length > 0) {
      link.mutate(
        { document_ids: selectedDocumentIds, folder_id: targetFolderId, mode: FOLDER_LINK_MODE.replace },
        { onSuccess: (result) => toast.success(folderBulkResultMessage('chuyển', result)) },
      )
    }
    onClearSelection()
  }

  return {
    total,
    hasFolders,
    overCap,
    overDocCap,
    overFolderCap,
    showDelete,
    canDeleteDocuments,
    runDelete,
    runUnlink,
    runAdd,
    runMoveTo,
  }
}
