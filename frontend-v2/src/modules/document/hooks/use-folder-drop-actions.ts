import { confirm } from '@/shared/ui/confirm-dialog'
import type { FolderDragPayload } from '../helpers/folder-drag-payload'
import {
  useLinkDocumentsToFolder,
  useMoveDocFolder,
  useUnlinkDocumentsFromFolder,
} from './use-document-folders'
import { FOLDER_LINK_MODE } from '../types/document-folder'
import type { DocumentRecord } from '../types/document-record'

/**
 * Hành động THAO TÁC THƯ MỤC dùng chung của khung nội dung — kéo thả nhận từ
 * ngoài vào một thẻ thư mục, và gỡ MỘT văn bản khỏi thư mục đang xem (menu
 * chuột phải / thẻ Lưới). Tách khỏi `folder-documents-table.tsx` để tệp đó
 * dưới 200 dòng.
 */
export function useFolderDropActions(folderId: number, folderName: string) {
  const link = useLinkDocumentsToFolder()
  const unlink = useUnlinkDocumentsFromFolder()
  const moveFolder = useMoveDocFolder()

  /**
   * Thả lên một thẻ/dòng thư mục. Văn bản mặc định CHUYỂN (gắn vào đích rồi
   * gỡ khỏi thư mục NGUỒN — chỉ thư mục nguồn, không đụng các thư mục khác văn
   * bản đang nằm); `keepInSource` (giữ Alt/Option) = THÊM một chỗ nữa. Đổi
   * 24/09/2026: mặc định cũ là THÊM, người dùng thấy văn bản «nhân bản».
   */
  function handleDropOnFolder(
    targetFolderId: number,
    payload: FolderDragPayload,
    keepInSource: boolean,
  ) {
    for (const sourceId of payload.folderIds) {
      if (sourceId !== targetFolderId)
        moveFolder.mutate({ id: sourceId, newParentId: targetFolderId })
    }
    if (payload.documentIds.length === 0) return
    const { sourceFolderId } = payload
    link.mutate(
      { document_ids: payload.documentIds, folder_id: targetFolderId, mode: FOLDER_LINK_MODE.add },
      {
        onSuccess: () => {
          if (!keepInSource && sourceFolderId != null && sourceFolderId !== targetFolderId) {
            unlink.mutate({ document_ids: payload.documentIds, folder_id: sourceFolderId })
          }
        },
      },
    )
  }

  async function handleRemoveDocument(document: DocumentRecord) {
    const ok = await confirm({
      message: `Gỡ «${document.title}» khỏi thư mục «${folderName}»? Văn bản vẫn còn nguyên ở các thư mục khác.`,
      confirmLabel: 'Gỡ',
    })
    if (ok) unlink.mutate({ document_ids: [document.id], folder_id: folderId })
  }

  return { handleDropOnFolder, handleRemoveDocument }
}
