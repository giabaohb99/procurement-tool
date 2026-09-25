import { usePermission } from '@/core/authorization/use-permission'
import { FilterProvider } from '@/shared/conditional-filter'
import { Skeleton } from '@/shared/ui/skeleton'
import { DOCUMENT_LIST_FILTER_FIELDS } from '../config/document-list-filter-fields'
import { folderItemKey } from '../helpers/folder-item-id'
import { FOLDER_VIEW_STORAGE_KEY } from '../helpers/folder-view-storage-key'
import { useFolderDocumentsTableState } from '../hooks/use-folder-documents-table-state'
import { FolderChildCards } from './folder-child-cards'
import { FolderDetailsPanel } from './folder-details-panel'
import { FolderDocumentsView } from './folder-documents-view'
import { FolderSelectionToolbar } from './folder-selection-toolbar'
import { FolderShareDialog } from './folder-share-dialog'
import { FolderViewToolbar } from './folder-view-toolbar'

//  Xuất lại ở đây (giữ TÊN CŨ) để nơi khác đang import từ tệp này (vd
//  `folder-my-drive-panel.tsx`, `folder-documents-table.test.tsx`) không phải
//  đổi đường dẫn — nguồn thật nằm ở `helpers/folder-view-storage-key.ts` (một
//  hằng THUẦN, không kéo theo import ngược từ tầng `hooks/`).
export const VIEW_STORAGE_KEY = FOLDER_VIEW_STORAGE_KEY

//  «Bộ lọc nâng cao» (đặc tả A, phản hồi 24/09/2026) — CÙNG `DOCUMENT_LIST_FILTER_FIELDS`
//  với danh sách Văn bản chung (`outgoing-documents-tab.tsx`). `preserveParams`
//  liệt kê MỌI tham số của trang thư mục + của chính bảng này — thiếu tên nào
//  là bấm "Áp dụng"/"Xóa lọc" ở bộ lọc nâng cao xóa mất tham số đó khỏi URL.
const FOLDER_DOCUMENTS_FILTER_CONFIG = {
  fields: DOCUMENT_LIST_FILTER_FIELDS,
  allowConjunctionToggle: true,
  preserveParams: ['folder', 'tab', 'doc', 'q', 'sub', 'full_text', 'page'],
}

interface FolderDocumentsTableProps {
  folderId: number
  folderName: string
  /** Bấm mở một thư mục con — chuyển trạng thái `?folder=` của TRANG (không phải điều hướng URL rời). */
  onSelectFolder: (id: number) => void
  /**
   * Tương thích ngược với lối vào «Phân quyền» cũ từ cây bên trái
   * (`?tab=access`, tab đã bỏ) — `true` thì mở NGAY hộp «Chia sẻ» của thư mục
   * đang xem. `folder-contents-panel.tsx` tự lo phần dọn tham số `tab` khỏi
   * URL (effect riêng của nó), không cần báo ngược lại qua đây.
   */
  openShareOnMount?: boolean
  /** Văn bản CÂY vừa chỉ tới (bấm một lá) — tự chọn + mở khung chi tiết + cuộn tới đúng dòng, rồi báo `onDocumentHandled`. */
  selectedDocumentId?: number | null
  onDocumentHandled?: () => void
}

/**
 * KHUNG NỘI DUNG kiểu Google Drive (đặc tả §B, phase 10B; toolbar làm lại
 * theo §P3 + phản hồi 24/09/2026) — Hàng 1 (`FolderViewToolbar`: tiêu đề + huy
 * hiệu + Chia sẻ/chuyển chế độ/chi tiết), rồi «Văn bản»
 * (`FolderDocumentsView`: Hàng 2 tìm/lọc + Lưới/Danh sách — sắp xếp nay bấm
 * thẳng cột/nhãn, không còn ô Select riêng). Chọn kiểu Drive (bấm/Ctrl/Shift/
 * Esc/Ctrl+A, hợp nhất cả hai loại thẻ), thanh thao tác THAY chỗ hàng tìm/lọc
 * khi có chọn, kéo thả nhận từ khung trái, khung chi tiết bật/tắt được.
 *
 * Bọc `FilterProvider` ở ĐÂY (không phải `folder-contents-panel.tsx`) vì «Bộ
 * lọc nâng cao» chỉ có ý nghĩa với bảng văn bản, không phải toàn khung phải.
 *
 * Toàn bộ state/hook nằm ở `use-folder-documents-table-state.ts` — tệp này
 * chỉ còn lo BỐ CỤC + nối props, dưới 200 dòng.
 */
export function FolderDocumentsTable(props: FolderDocumentsTableProps) {
  return (
    <FilterProvider config={FOLDER_DOCUMENTS_FILTER_CONFIG}>
      <FolderDocumentsTableContent {...props} />
    </FilterProvider>
  )
}

function FolderDocumentsTableContent({
  folderId,
  folderName,
  onSelectFolder,
  openShareOnMount = false,
  selectedDocumentId,
  onDocumentHandled,
}: FolderDocumentsTableProps) {
  const { can } = usePermission()
  const s = useFolderDocumentsTableState({
    folderId,
    folderName,
    openShareOnMount,
    selectedDocumentId,
    onDocumentHandled,
  })

  return (
    <div className="flex min-h-0 flex-1 gap-3">
      <div className="min-w-0 flex-1 space-y-3">
        {s.folder ? (
          <FolderViewToolbar
            folder={s.folder}
            isGrid={s.isGrid}
            onToggleGrid={(next) => next !== s.isGrid && s.flipGrid()}
            detailsOpen={s.detailsOpen}
            onToggleDetails={() => s.setDetailsOpen((v) => !v)}
            onShare={() => s.openShare(folderId)}
          />
        ) : (
          <Skeleton className="h-9 w-full" />
        )}

        <FolderDocumentsView
          isGrid={s.isGrid}
          folderId={folderId}
          q={s.q}
          documentTypes={s.documentTypes}
          folderCards={
            //  Chế độ Lưới giữ khối thẻ thư mục RIÊNG (đặc tả C), vẽ DƯỚI hàng
            //  tìm/lọc (chốt 24/09/2026 — trước đây nằm trên, ô tìm bị đẩy
            //  xuống giữa trang). Chế độ Danh sách gộp thư mục vào chung bảng.
            s.isGrid && s.children.length > 0 ? (
              <div className="space-y-1.5">
                <h3 className="text-sm font-semibold">
                  Thư mục{' '}
                  <span className="font-normal text-muted-foreground">({s.children.length})</span>
                </h3>
                <FolderChildCards
                  children={s.children}
                  sourceFolderId={folderId}
                  isSelected={s.selection.isSelected}
                  onItemClick={(id, modifiers) =>
                    s.selection.handleClick(folderItemKey('folder', id), modifiers)
                  }
                  onOpen={onSelectFolder}
                  onViewDetails={s.viewFolderDetails}
                  onDropItems={s.handleDropOnFolder}
                />
              </div>
            ) : null
          }
          selectionToolbar={
            s.hasSelection ? (
              <FolderSelectionToolbar
                selectedFolderIds={s.selectedFolderIds}
                selectedDocumentIds={s.selectedDocumentIds}
                currentFolder={{ id: folderId, name: folderName }}
                onClearSelection={s.selection.clear}
                onShowDetails={() => s.setDetailsOpen(true)}
              />
            ) : null
          }
          sortField={s.sortField}
          sortDir={s.sortDir}
          onSortFieldChange={s.setSortField}
          onToggleSortDir={() => s.setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))}
          selection={s.selection}
          onOpenDocument={s.openDocument}
          onViewDetails={s.viewDocumentDetails}
          onRemoveDocument={s.handleRemoveDocument}
          canWrite={can('document', 'write')}
          canDelete={can('document', 'write')}
          children={s.isGrid ? [] : s.children}
          onOpenFolder={onSelectFolder}
          onViewFolderDetails={s.viewFolderDetails}
          onDropOnFolder={s.handleDropOnFolder}
        />
      </div>

      {s.detailsOpen && (
        <FolderDetailsPanel
          item={s.detailsItem}
          onClose={() => s.setDetailsOpen(false)}
          onOpenDocument={() =>
            s.detailsItem.kind === 'document' && s.openDocument(s.detailsItem.document)
          }
          onManagePermissions={() =>
            s.detailsItem.kind === 'folder' && s.openShare(s.detailsItem.folder.id)
          }
        />
      )}

      {s.shareFolderId != null && (
        <FolderShareDialog
          folderId={s.shareFolderId}
          open
          onOpenChange={(open) => !open && s.closeShare()}
          onNavigateToFolder={(id) => {
            s.closeShare()
            onSelectFolder(id)
          }}
        />
      )}
    </div>
  )
}
