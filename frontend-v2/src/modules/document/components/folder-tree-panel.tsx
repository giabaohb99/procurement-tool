import { useEffect, useRef } from 'react'

import { TreeView } from '@/shared/tree/tree-view'
import { Input } from '@/shared/ui/input'
import { Skeleton } from '@/shared/ui/skeleton'
import { ancestorIdsOfMatches } from '../helpers/folder-tree-search'
import { useFolderDragMove } from '../hooks/use-folder-drag-move'
import { useFolderTreeActions } from '../hooks/use-folder-tree-actions'
import { useFolderTreeDrag } from '../hooks/use-folder-tree-drag'
import { useFolderTreeNavigation } from '../hooks/use-folder-tree-navigation'
import { useFolderTreeNodes } from '../hooks/use-folder-tree-nodes'
import { useFolderTreeSearchBox } from '../hooks/use-folder-tree-search-box'
import { useDocFolderTree } from '../hooks/use-document-folders'
import { usePersistedFolderTreeExpansion } from '../hooks/use-persisted-folder-tree-expansion'
import { usePersistedTreeDisplayOptions } from '../hooks/use-persisted-tree-display-options'
import { FOLDER_ACCESS_LEVEL, FOLDER_KIND } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'
import { FolderTreeNewMenu } from './folder-tree-new-menu'
import { FolderTreePanelDialogs } from './folder-tree-panel-dialogs'
import { FolderTreePanelHeader } from './folder-tree-panel-header'
import { usePermission } from '@/core/authorization/use-permission'
import { buildFolderTreeRowRenderers, canManageNode } from './folder-tree-row-renderers'

const COMPANY_GROUP_OPENED_KEY = 'erp.document.folders.company-group-opened'

export interface FolderTreePanelProps {
  selectedFolderId: number | null
  onSelectFolder: (id: number) => void
  /**
   * Bấm/Enter một LÁ VĂN BẢN trong cây (duoc-CR-476, yêu cầu 23/09/2026 tối) —
   * mở ĐÚNG thư mục cha đó ở khung phải và chọn sẵn văn bản này (khung phải tự
   * mở khung chi tiết + cuộn tới đúng dòng). KHÔNG điều hướng rời trang — muốn
   * mở hẳn trang chi tiết văn bản thì bấm ĐÚP/Enter (xem `handleActivate`).
   */
  onSelectDocument: (folderId: number, documentId: number) => void
  /** Bấm "Chia sẻ…" ở menu — chọn thư mục đó VÀ chuyển khung phải sang `?tab=access` (khung phải tự mở hộp «Chia sẻ» kiểu Drive). */
  onOpenAccessTab: (folderId: number) => void
  /** Chỉ có khi dựng trong `FolderTreePanelShell` (desktop) — thêm một nút "Thu gọn khung" ở tiêu đề. */
  onCollapsePanel?: () => void
  /** Bấm nhãn «THƯ MỤC» ở đầu cây — bỏ chọn, về gốc «Thư mục của bạn». */
  onSelectRoot?: () => void
}

/**
 * KHUNG TRÁI — cây thư mục văn bản, kiểu VS Code Explorer (duoc-CR-476, yêu
 * cầu 23/09/2026). Gốc là các pháp nhân mình thấy, dưới đó là thư mục rồi văn
 * bản trực tiếp (lá lười tải khi mở, `useFolderTreeNodes`) — luật hiển
 * thị/thao tác đọc từ `my_level` backend tính sẵn trên MỖI nút, không tự suy
 * đoán. State/mutation nằm ở `useFolderTreeActions` (đổi tên · tạo mới tại
 * chỗ · chuyển · xóa), `useFolderDragMove`/`useFolderTreeDrag` (kéo thả) và
 * `useFolderTreeSearchBox` (ô lọc gọn) — tách ra để tệp này dưới 200 dòng.
 */
export function FolderTreePanel({
  selectedFolderId,
  onSelectFolder,
  onSelectDocument,
  onOpenAccessTab,
  onCollapsePanel,
  onSelectRoot,
}: FolderTreePanelProps) {
  const { includeArchived, setIncludeArchived, showDocuments, setShowDocuments } =
    usePersistedTreeDisplayOptions()
  const search = useFolderTreeSearchBox()
  const searchInputRef = useRef<HTMLInputElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (search.searchOpen) searchInputRef.current?.focus()
  }, [search.searchOpen])
  const { data: rows, isLoading, isFetching, refetch } = useDocFolderTree(includeArchived)
  const expansion = usePersistedFolderTreeExpansion()
  //  Nhóm «Công ty» (24/09/2026) — mở sẵn MỘT LẦN cho mỗi máy, để thư mục pháp
  //  nhân không "biến mất" sau đợt dời vào nhóm. Người dùng gập lại thì thôi,
  //  không tự bung lại mỗi lần vào trang.
  const companyGroupId = rows?.find((row) => row.kind === FOLDER_KIND.companyGroup)?.id
  const expandFolder = expansion.expand
  useEffect(() => {
    if (companyGroupId == null) return
    try {
      if (localStorage.getItem(COMPANY_GROUP_OPENED_KEY)) return
      localStorage.setItem(COMPANY_GROUP_OPENED_KEY, '1')
    } catch {
      //  Trình duyệt chặn storage — vẫn mở, chỉ không nhớ là đã mở.
    }
    expandFolder(companyGroupId)
  }, [companyGroupId, expandFolder])

  const actions = useFolderTreeActions()
  const { can } = usePermission()
  //  `folderDrag` giữ NGUYÊN hình dạng của `useFolderDragMove` (còn
  //  `pendingDrop`/`confirmPendingDrop`/`cancelPendingDrop` cho hộp xác nhận ở
  //  `FolderTreePanelDialogs`) — `treeDrag` là bản GỘP thêm kéo lá văn bản,
  //  chỉ dùng để spread vào `TreeView`.
  const folderDrag = useFolderDragMove(rows)
  const treeDrag = useFolderTreeDrag(folderDrag)

  const canStartRename = (node: DocFolderTreeNode) => node.my_level >= FOLDER_ACCESS_LEVEL.manage

  /** Mở dòng nhập TẠM «thư mục mới» — xóa từ khóa tìm (chắc chắn cha còn hiện) + mở sẵn cha. */
  function beginCreate(node: DocFolderTreeNode) {
    search.close()
    expansion.expand(node.id)
    actions.startCreate(node)
  }

  /** Dòng nhập «thư mục mới» ở GỐC cây — thư mục tự do, không thuộc pháp nhân nào. */
  function beginCreateAtRoot() {
    search.close()
    actions.startCreateAtRoot()
  }

  const selectedNode = rows?.find((row) => row.id === selectedFolderId)
  //  Chưa chọn thư mục nào = đang đứng ở GỐC → «Thư mục mới» tạo thư mục tự do
  //  ở gốc (mở 24/09/2026), chỉ cần quyền `doc_folder.create`.
  const atRoot = selectedFolderId == null
  const canCreateHere = atRoot
    ? can('doc_folder', 'create')
    : Boolean(selectedNode && canManageNode(selectedNode))
  const createHere = () =>
    atRoot ? beginCreateAtRoot() : selectedNode && beginCreate(selectedNode)
  const { visibleTree, leaves, matchedIds, rowsById, effectiveSelectedId } = useFolderTreeNodes({
    rows,
    keyword: search.keyword,
    expandedIds: expansion.expandedIds,
    creatingUnder: actions.creatingUnder,
    selectedFolderId,
    showDocuments,
  })

  //  Gõ ra kết quả thì tự MỞ đủ tổ tiên của mọi dòng khớp — không thì người
  //  tìm thấy 0 kết quả dù dữ liệu có, chỉ vì nhánh chứa nó đang gập.
  useEffect(() => {
    if (!search.keyword.trim() || !rows) return
    const ancestorIds = ancestorIdsOfMatches(rows, matchedIds)
    if (ancestorIds.length) expansion.expandAncestors(ancestorIds)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chỉ chạy lại khi TỪ KHÓA đổi, không phải mỗi lần expandedIds đổi (mở tay một nhánh không nên bị ghi đè)
  }, [search.keyword, rows])

  const { handleSelect, handleActivate, handleRowDoubleClick } = useFolderTreeNavigation({
    selectedFolderId,
    rows,
    leaves,
    expandAncestors: expansion.expandAncestors,
    expandedIds: expansion.expandedIds,
    scrollContainerRef,
    onSelectFolder,
    onSelectDocument,
  })

  if (isLoading) {
    return (
      <div className="space-y-2 p-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-6 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col gap-1">
      <div className="p-2 pb-0">
        <FolderTreeNewMenu
          folderId={selectedFolderId}
          canCreateFolder={canCreateHere}
          onCreateFolder={createHere}
        />
      </div>

      <FolderTreePanelHeader
        canCreate={canCreateHere}
        onCreate={createHere}
        onCollapseAll={expansion.collapseAll}
        onRefresh={() => void refetch()}
        refreshing={isFetching}
        onCollapsePanel={onCollapsePanel}
        searchOpen={search.searchOpen}
        onToggleSearch={search.toggle}
        includeArchived={includeArchived}
        onIncludeArchivedChange={setIncludeArchived}
        showDocuments={showDocuments}
        onShowDocumentsChange={setShowDocuments}
        onSelectRoot={onSelectRoot}
        atRoot={selectedFolderId == null}
        rootDrop={{ canDrop: folderDrag.canDropOnRoot, onDrop: folderDrag.dropOnRoot }}
      />

      {search.searchOpen && (
        <div className="px-2">
          <Input
            ref={searchInputRef}
            value={search.keyword}
            onChange={(event) => search.setKeyword(event.target.value)}
            onKeyDown={(event) => event.key === 'Escape' && search.close()}
            placeholder="Tìm thư mục…"
            className="h-7 text-xs"
            aria-label="Tìm thư mục"
          />
        </div>
      )}

      <div
        ref={scrollContainerRef}
        className="min-h-0 flex-1 overflow-y-auto pb-2"
        onKeyDown={(event) => {
          //  F2 sửa TẠI CHỖ thư mục đang CHỌN — TreeView không tự bắt phím này
          //  (nó chỉ xử lý điều hướng), sự kiện nổi bọt lên tới đây thì bắt tiếp.
          if (event.key !== 'F2' || selectedFolderId == null) return
          const node = rows?.find((row) => row.id === selectedFolderId)
          if (node && canStartRename(node)) actions.startRename(node)
        }}
      >
        {visibleTree.length === 0 ? (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">
            {search.keyword.trim()
              ? 'Không có thư mục nào khớp từ khóa đang tìm.'
              : 'Chưa có thư mục nào.'}
          </p>
        ) : (
          <TreeView
            nodes={visibleTree}
            ariaLabel="Cây thư mục văn bản"
            selectedId={effectiveSelectedId}
            onSelect={handleSelect}
            onActivate={handleActivate}
            onRowDoubleClick={(node) =>
              handleRowDoubleClick(node, canStartRename, actions.startRename)
            }
            expandedIds={expansion.expandedIds}
            onToggleExpand={expansion.toggle}
            highlightIds={search.keyword.trim() ? matchedIds : undefined}
            {...treeDrag}
            {...buildFolderTreeRowRenderers({
              expansion,
              actions,
              keyword: search.keyword,
              beginCreate,
              onSelectFolder,
              onOpenAccessTab,
              leaves,
              rowsById,
            })}
          />
        )}
      </div>

      <FolderTreePanelDialogs actions={actions} drag={folderDrag} rows={rows} />
    </div>
  )
}
