import { FolderGridDocumentCard } from './folder-grid-document-card'
import { FolderItemContextMenu } from './folder-item-context-menu'
import { writeFolderDragPayload } from '../helpers/folder-drag-payload'
import { folderItemKey } from '../helpers/folder-item-id'
import type { SelectionModifierKeys } from '../hooks/use-item-selection'
import type { DocumentRecord } from '../types/document-record'

interface FolderGridViewProps {
  documents: DocumentRecord[]
  /** Thư mục ĐANG XEM — nguồn của lượt kéo (gắn vào `dataTransfer`). */
  sourceFolderId: number
  isSelected: (key: string) => boolean
  onItemClick: (id: number, modifiers: SelectionModifierKeys) => void
  onOpen: (document: DocumentRecord) => void
  onViewDetails: (document: DocumentRecord) => void
  onMoveTo: (document: DocumentRecord) => void
  /** «Chia sẻ…» — mở hộp quyền truy cập của đúng văn bản đó. */
  onShare: (document: DocumentRecord) => void
  onRemove: (document: DocumentRecord) => void
  canWrite: boolean
  canDelete: boolean
}

/**
 * CHẾ ĐỘ LƯỚI của bảng «Văn bản» trong khung nội dung thư mục (đặc tả §B) —
 * thay `DataTable` khi người dùng bật «Lưới». Cùng cơ chế chọn/kéo/menu chuột
 * phải với chế độ danh sách, khác mỗi cách trình bày một dòng.
 *
 * ⚠️ `canWrite`/`canDelete` là quyền THEO VAI TRÒ (`document.write/delete`),
 * KHÔNG phải quyền trên ĐÚNG văn bản này — hỏi quyền riêng từng dòng
 * (`GET /documents/{id}/permissions`) cho một trang vài chục thẻ là N+1 lượt
 * gọi. Cùng nhân nhượng "chỉ ẩn nút, không phải hàng rào bảo mật" mà
 * `document-copy-action.tsx` đã chấp nhận — backend vẫn tự gác lại lần nữa.
 */
export function FolderGridView({
  documents,
  sourceFolderId,
  isSelected,
  onItemClick,
  onOpen,
  onViewDetails,
  onMoveTo,
  onShare,
  onRemove,
  canWrite,
  canDelete,
}: FolderGridViewProps) {
  if (documents.length === 0) return null

  return (
    //  Ô co giãn theo BỀ RỘNG THẬT của khung (`auto-fill`/`minmax`) thay vì
    //  bậc thang theo breakpoint màn hình — đặc tả §P4, chốt UI 23/09/2026:
    //  khung chi tiết bật lên thu hẹp cột nội dung thì lưới vẫn tự co đúng số
    //  cột vừa khít, không đợi qua breakpoint kế tiếp mới đổi.
    <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3">
      {documents.map((document) => (
        <FolderItemContextMenu
          key={document.id}
          kind="document"
          canWriteDocument={canWrite}
          canDeleteDocument={canDelete}
          showMenuButton
          menuButtonPlacement="corner"
          onOpen={() => onOpen(document)}
          onMoveTo={() => onMoveTo(document)}
          onManagePermissions={() => onShare(document)}
          onViewDetails={() => onViewDetails(document)}
          onRemove={() => onRemove(document)}
        >
          <div
            draggable
            onDragStart={(event) =>
              writeFolderDragPayload(event.dataTransfer, {
                documentIds: [document.id],
                folderIds: [],
                sourceFolderId,
              })
            }
          >
            <FolderGridDocumentCard
              document={document}
              selected={isSelected(folderItemKey('document', document.id))}
              onClick={(modifiers) => onItemClick(document.id, modifiers)}
              onOpen={() => onOpen(document)}
            />
          </div>
        </FolderItemContextMenu>
      ))}
    </div>
  )
}
