import { useState } from 'react'

import { usePersistedToggle } from '@/shared/hooks/use-persisted-toggle'
import { Skeleton } from '@/shared/ui/skeleton'
import { folderItemKey } from '../helpers/folder-item-id'
import {
  DOCUMENT_SORT_FIELD,
  type DocumentSortField,
  type SortDirection,
} from '../helpers/sort-document-rows'
import { FOLDER_VIEW_STORAGE_KEY } from '../helpers/folder-view-storage-key'
import { useFolderContentSelection } from '../hooks/use-folder-content-selection'
import { useFolderDetailsItem } from '../hooks/use-folder-details-item'
import { useFolderDropActions } from '../hooks/use-folder-drop-actions'
import { useDocFolderTree } from '../hooks/use-document-folders'
import { useFolderShareTarget } from '../hooks/use-folder-share-target'
import type { DocFolderTreeNode } from '../types/document-folder'
import { FolderChildCards } from './folder-child-cards'
import { FolderDetailsPanel } from './folder-details-panel'
import { FolderListView } from './folder-list-view'
import { FolderShareDialog } from './folder-share-dialog'
import { FolderViewModeControls } from './folder-view-mode-controls'

interface FolderMyDrivePanelProps {
  onSelectFolder: (id: number) => void
}

/**
 * Trạng thái CHƯA CHỌN THƯ MỤC nào ở khung phải, kiểu «Drive của tôi» (đặc tả
 * §B, duoc-CR-476, phản hồi 24/09/2026: bản cũ vẽ thẻ RIÊNG to-cao-căn-giữa,
 * khác hẳn khối bên trong một thư mục thật — nay REUSE Y NGUYÊN hai renderer
 * của một thư mục thật: chế độ Lưới → `FolderChildCards` (thẻ pill gọn),
 * Danh sách → `FolderListView` (dòng kiểu Drive). Mỗi thư mục PHÁP NHÂN
 * (`kind = COMPANY`) mình thấy được hiện thành MỘT thẻ/dòng như một thư mục
 * con bình thường — cùng chọn (bấm/Ctrl/Shift/Esc/Ctrl+A), cùng menu chuột
 * phải, cùng khung chi tiết, cùng đích thả kéo. Bấm ĐÚP/Enter mở thư mục pháp
 * nhân đó vào khung phải (`onSelectFolder`), y hệt mở một thư mục con.
 *
 * `FolderChildCards`/`FolderListView` đã tự đọc `my_level` để ẩn Đổi
 * tên/Chuyển tới cho thư mục pháp nhân (`isCompanyRoot`) và tự cho phép Xóa
 * khi RỖNG + đủ quyền Quản lý (`folder-delete-disabled-reason.ts`) — không
 * cần logic riêng ở tệp này cho hai việc đó.
 *
 * Chế độ Lưới/Danh sách dùng CHUNG `FOLDER_VIEW_STORAGE_KEY` với một thư mục
 * thật (`folder-documents-table.tsx`) — đổi chế độ ở gốc rồi mở một thư mục,
 * hay ngược lại, phải giữ nguyên chế độ, không nhảy về mặc định.
 *
 * KHÔNG có thanh thao tác hàng loạt (`FolderSelectionToolbar`) ở đây — thư
 * mục pháp nhân không "Thêm vào"/"Gỡ khỏi" được (không có `currentFolder`) và
 * backend chặn cứng việc CHUYỂN chúng sang cha khác, nên phần còn lại (chỉ
 * «Xóa» hàng loạt) không đủ giá trị để thêm một thanh riêng — xóa từng cái
 * qua menu ⋯ vẫn dùng được bình thường.
 */
export function FolderMyDrivePanel({ onSelectFolder }: FolderMyDrivePanelProps) {
  const { data: rows, isLoading } = useDocFolderTree()
  //  Mọi thư mục ở GỐC cây — pháp nhân LẪN thư mục tự do tạo ở gốc (lỗi
  //  24/09/2026: lọc `kind === company` làm thư mục tự do không hiện ở đây).
  const roots = (rows ?? []).filter((row) => row.parent_id === 0)

  const [isGrid, flipGrid] = usePersistedToggle(FOLDER_VIEW_STORAGE_KEY, false)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [sortField, setSortField] = useState<DocumentSortField>(DOCUMENT_SORT_FIELD.name)
  const [sortDir, setSortDir] = useState<SortDirection>('asc')
  //  Không có "thư mục đang xem" ở gốc để làm mặc định — cả hai hook dưới đây
  //  chỉ dùng cho tương thích ngược lối vào cũ (mở kèm `openOnMount`/gỡ khỏi
  //  MỘT thư mục cụ thể), không áp dụng ở màn này nên truyền placeholder rồi
  //  luôn gọi `openShare(id)`/không bao giờ gọi `handleRemoveDocument`.
  const { shareFolderId, openShare, closeShare } = useFolderShareTarget(0, false)
  const { handleDropOnFolder } = useFolderDropActions(0, '')

  const selection = useFolderContentSelection({
    folderKeys: roots.map((root) => folderItemKey('folder', root.id)),
    documentKeys: [],
    resetSignal: roots.length,
  })

  function viewDetails(root: Pick<DocFolderTreeNode, 'id'>) {
    selection.selectOnly(folderItemKey('folder', root.id))
    setDetailsOpen(true)
  }

  const detailsItem = useFolderDetailsItem(selection.selectedIds, undefined, [])

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-2 p-4 sm:grid-cols-3 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-9 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-0 gap-3 p-4">
      <div className="min-w-0 flex-1 space-y-3">
        <div className="flex items-center justify-between gap-2 border-b pb-3">
          <h2 className="text-base font-semibold">Thư mục của bạn</h2>
          <FolderViewModeControls
            isGrid={isGrid}
            onToggleGrid={(next) => next !== isGrid && flipGrid()}
            detailsOpen={detailsOpen}
            onToggleDetails={() => setDetailsOpen((v) => !v)}
          />
        </div>

        {roots.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            Bạn chưa thấy thư mục pháp nhân nào — liên hệ quản trị để được cấp quyền.
          </p>
        ) : isGrid ? (
          <FolderChildCards
            children={roots}
            sourceFolderId={null}
            isSelected={selection.isSelected}
            onItemClick={(id, modifiers) =>
              selection.handleClick(folderItemKey('folder', id), modifiers)
            }
            onOpen={onSelectFolder}
            onViewDetails={viewDetails}
            onDropItems={handleDropOnFolder}
            selectable={false}
          />
        ) : (
          <FolderListView
            children={roots}
            documents={[]}
            sourceFolderId={null}
            isFullText={false}
            sortField={sortField}
            sortDir={sortDir}
            onSortFieldChange={setSortField}
            onToggleSortDir={() => setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))}
            selection={selection}
            onOpenFolder={onSelectFolder}
            //  Không bao giờ được gọi — gốc không liệt kê văn bản nào (`documents=[]`).
            onOpenDocument={() => undefined}
            onViewFolderDetails={viewDetails}
            onViewDocumentDetails={() => undefined}
            onDropOnFolder={handleDropOnFolder}
            onMoveDocumentTo={() => undefined}
            onRemoveDocument={() => undefined}
            canWrite={false}
            canDelete={false}
            selectable={false}
          />
        )}
      </div>

      {detailsOpen && (
        <FolderDetailsPanel
          item={detailsItem}
          onClose={() => setDetailsOpen(false)}
          onManagePermissions={() =>
            detailsItem.kind === 'folder' && openShare(detailsItem.folder.id)
          }
        />
      )}

      {shareFolderId != null && (
        <FolderShareDialog
          folderId={shareFolderId}
          open
          onOpenChange={(open) => !open && closeShare()}
          onNavigateToFolder={(id) => {
            closeShare()
            onSelectFolder(id)
          }}
        />
      )}
    </div>
  )
}
