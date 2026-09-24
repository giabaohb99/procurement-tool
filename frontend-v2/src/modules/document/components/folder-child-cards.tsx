import { useMemo, useState } from 'react'

import { cn } from '@/shared/utils/cn'
import { FolderNodeIcon } from './folder-tree-item'
import { FolderItemContextMenu } from './folder-item-context-menu'
import { FolderItemSelectCheckbox } from './folder-item-select-checkbox'
import { FolderRowActionDialogs } from './folder-row-action-dialogs'
import { folderDeleteDisabledReason } from '../helpers/folder-delete-disabled-reason'
import {
  hasFolderDragPayload,
  readFolderDragPayload,
  writeFolderDragPayload,
  type FolderDragPayload,
} from '../helpers/folder-drag-payload'
import { countSubfoldersByParent, formatFolderContentCount } from '../helpers/folder-content-count'
import { dispatchFolderItemClick, readModifierKeys } from '../helpers/folder-item-click'
import { folderItemKey } from '../helpers/folder-item-id'
import { useDocFolderTree } from '../hooks/use-document-folders'
import { useFolderRowActions } from '../hooks/use-folder-row-actions'
import type { SelectionModifierKeys } from '../hooks/use-item-selection'
import { canBulkSelectFolder, FOLDER_KIND } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'

interface FolderChildCardsProps {
  children: DocFolderTreeNode[]
  /**
   * Thư mục ĐANG XEM — nguồn của lượt kéo khi thả thẻ này ra ngoài. `null` =
   * không gắn với một thư mục cụ thể (gốc «Thư mục của bạn», các thẻ ở đây là
   * THƯ MỤC PHÁP NHÂN — kéo ra khỏi "không đâu cả" chứ không phải khỏi một
   * thư mục cha thật).
   */
  sourceFolderId: number | null
  isSelected: (key: string) => boolean
  onItemClick: (id: number, modifiers: SelectionModifierKeys) => void
  onOpen: (id: number) => void
  onViewDetails: (folder: DocFolderTreeNode) => void
  /**
   * Thả văn bản/thư mục khác LÊN một thẻ ở đây — nơi gọi tự quyết định gọi API
   * nào. `keepInSource` = giữ Alt/Option lúc thả (đổi 24/09/2026: mặc định
   * CHUYỂN văn bản, giữ Alt = THÊM một chỗ nữa).
   */
  onDropItems: (targetFolderId: number, payload: FolderDragPayload, keepInSource: boolean) => void
  /** `false` = không vẽ ô tick trên thẻ (gốc «Thư mục của bạn»). Mặc định `true`. */
  selectable?: boolean
}

/**
 * Thư mục CON dạng thẻ, đầu tab «Văn bản» của khung nội dung — kiểu Drive
 * (đặc tả §B): chọn được (bấm/Ctrl/Shift), kéo được ra ngoài, nhận thả từ
 * ngoài vào, menu chuột phải đủ sáu mục theo `my_level`.
 */
export function FolderChildCards({
  children,
  sourceFolderId,
  isSelected,
  onItemClick,
  onOpen,
  onViewDetails,
  onDropItems,
  selectable = true,
}: FolderChildCardsProps) {
  const [dragOverId, setDragOverId] = useState<number | null>(null)
  const rowActions = useFolderRowActions()
  //  Cây đã được nơi gọi nạp sẵn (cùng query key) — không phát thêm request.
  const { data: allFolders } = useDocFolderTree()
  const subfolderCounts = useMemo(() => countSubfoldersByParent(allFolders), [allFolders])

  if (children.length === 0) return null

  return (
    <>
      {/*  Thẻ thư mục kiểu Google Drive (làm lại 24/09/2026): nền xám nhạt
          KHÔNG viền, bo `rounded-xl`, icon + tên + dòng phụ đếm «n thư mục ·
          n văn bản», nút «⋮» LUÔN hiện. Có viền + bóng nhẹ như thẻ văn bản
          (bản nền xám không viền chìm vào nền trắng). Thay thẻ pill viền tròn cũ — lưới 4
          cột toàn viền nhìn như dãy ô nhập liệu. Chọn tô `bg-accent`/
          `ring-primary` cùng ngôn ngữ với thẻ Lưới văn bản. */}
      <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3">
        {children.map((child) => {
          const key = folderItemKey('folder', child.id)
          const selected = isSelected(key)
          const showCheckbox = selectable && canBulkSelectFolder(child)
          const countId = `folder-card-count-${child.id}`
          return (
            <FolderItemContextMenu
              key={child.id}
              kind="folder"
              myLevel={child.my_level}
              isCompanyRoot={child.kind === FOLDER_KIND.company}
              showMenuButton
              menuButtonAlwaysVisible
              onOpen={() => onOpen(child.id)}
              onRename={() => rowActions.setRenameTarget(child)}
              onMoveTo={() => rowActions.setMoveTarget(child)}
              onManagePermissions={() => rowActions.setShareTargetId(child.id)}
              onViewDetails={() => onViewDetails(child)}
              onRemove={() => void rowActions.requestDelete(child)}
              removeDisabledReason={folderDeleteDisabledReason(child)}
            >
              {showCheckbox && (
                <FolderItemSelectCheckbox
                  checked={selected}
                  onToggle={() => onItemClick(child.id, { ctrlKey: true })}
                  label={`Chọn ${child.display_name ?? child.name}`}
                  className="absolute top-1/2 left-3 z-10 -translate-y-1/2"
                />
              )}
              <button
                type="button"
                aria-label={child.display_name ?? child.name}
                aria-describedby={countId}
                draggable
                onDragStart={(event) =>
                  writeFolderDragPayload(event.dataTransfer, {
                    documentIds: [],
                    folderIds: [child.id],
                    sourceFolderId,
                  })
                }
                onDragOver={(event) => {
                  if (!hasFolderDragPayload(event.dataTransfer)) return
                  event.preventDefault()
                  setDragOverId(child.id)
                }}
                onDragLeave={() =>
                  setDragOverId((current) => (current === child.id ? null : current))
                }
                onDrop={(event) => {
                  event.preventDefault()
                  setDragOverId(null)
                  const payload = readFolderDragPayload(event.dataTransfer)
                  if (!payload) return
                  onDropItems(child.id, payload, event.altKey)
                }}
                onClick={(event) =>
                  dispatchFolderItemClick(readModifierKeys(event), {
                    onSelect: (modifiers) => onItemClick(child.id, modifiers),
                    onOpen: () => onOpen(child.id),
                  })
                }
                onKeyDown={(event) => {
                  //  ⚠️ `<button>` THẬT tự phát sinh `click` khi Enter/Space
                  //  (chọn) — thiếu dòng này thì Enter KHÔNG BAO GIỜ mở được
                  //  thư mục, chỉ chọn, khác hẳn hai chế độ kia (`FolderListRow`/
                  //  `FolderGridDocumentCard` dùng `<div role="button">` nên tự
                  //  viết tay `onKeyDown`, không dính hành vi mặc định này —
                  //  người dùng báo "bấm vào thư mục không nhảy" 24/09/2026 tối,
                  //  đúng đường Enter trên thẻ pill).
                  if (event.key === 'Enter') {
                    event.preventDefault()
                    onOpen(child.id)
                  }
                }}
                className={cn(
                  showCheckbox ? 'pl-9' : 'pl-2.5',
                  'flex w-full min-w-0 items-center gap-3 rounded-xl border bg-card py-2.5 pr-9 text-left shadow-xs transition-colors hover:border-primary/40 hover:bg-accent/40',
                  selected && 'border-primary bg-accent ring-1 ring-primary hover:bg-accent',
                  dragOverId === child.id && 'border-primary bg-accent ring-1 ring-primary',
                )}
              >
                {/*  Icon đen TRƠN, không ô nền/đệm (chốt 24/09/2026). */}
                <FolderNodeIcon data={child} className="size-5" />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-semibold">
                    {child.display_name ?? child.name}
                  </span>
                  <span id={countId} className="block truncate text-xs text-muted-foreground">
                    {formatFolderContentCount(
                      subfolderCounts.get(child.id) ?? 0,
                      child.document_count_branch,
                    )}
                  </span>
                </span>
              </button>
            </FolderItemContextMenu>
          )
        })}
      </div>

      <FolderRowActionDialogs actions={rowActions} onNavigateToFolder={onOpen} />
    </>
  )
}
