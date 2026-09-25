import { Share2 } from 'lucide-react'

import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { nameInitials } from '@/shared/utils/name-initials'
import { folderDeleteDisabledReason } from '../helpers/folder-delete-disabled-reason'
import {
  hasFolderDragPayload,
  readFolderDragPayload,
  writeFolderDragPayload,
  type FolderDragPayload,
} from '../helpers/folder-drag-payload'
import { dispatchFolderItemClick, readModifierKeys } from '../helpers/folder-item-click'
import { folderItemDomId } from '../helpers/folder-item-id'
import type { SelectionModifierKeys } from '../hooks/use-item-selection'
import { canBulkSelectFolder, FOLDER_KIND } from '../types/document-folder'
import type { DocFolderTreeNode } from '../types/document-folder'
import type { DocumentRecord } from '../types/document-record'
import { FolderItemContextMenu } from './folder-item-context-menu'
import { FolderItemSelectCheckbox } from './folder-item-select-checkbox'
import { Cell, NameCell } from './folder-list-row-cells'
import { effectiveStatusBadge } from './outgoing-document-columns'

/**
 * Cột thẳng hàng với dòng tiêu đề của `FolderListView` — Tên (co giãn) · Người
 * soạn · Ngày tạo · Trạng thái · vùng thao tác. Đo theo bề ngang của CHÍNH
 * khung danh sách (`@container` ở `FolderListView`), không theo màn hình: khung
 * phải thường chỉ ~650px vì còn menu ERP + cây bên trái, ba cột cố định cũ
 * (170+120+130px) ép cột Tên còn ~120px, tên văn bản cụt sau vài chữ (lỗi đại
 * ca bắt 24/09/2026). Khung hẹp thì GIẤU cột Người soạn — kiểu Drive giấu cột
 * «Chủ sở hữu» — để Tên được phần còn lại.
 */
export const FOLDER_LIST_GRID_TEMPLATE =
  'grid grid-cols-[1rem_minmax(0,1fr)_6rem_6.5rem_2rem] @2xl:grid-cols-[1rem_minmax(0,1fr)_10rem_6rem_7rem_2rem] items-center gap-3'

/** Cùng khuôn nhưng KHÔNG có cột ô tick đầu dòng — gốc «Thư mục của bạn» (chốt 24/09/2026: gốc không chọn hàng loạt). */
export const FOLDER_LIST_GRID_TEMPLATE_NO_SELECT =
  'grid grid-cols-[minmax(0,1fr)_6rem_6.5rem_2rem] @2xl:grid-cols-[minmax(0,1fr)_10rem_6rem_7rem_2rem] items-center gap-3'

/** Cột Người soạn chỉ hiện khi khung danh sách đủ rộng — xem `FOLDER_LIST_GRID_TEMPLATE`. */
export const FOLDER_LIST_OWNER_COLUMN = 'hidden @2xl:flex'

export type FolderListItem =
  { kind: 'folder'; folder: DocFolderTreeNode } | { kind: 'document'; document: DocumentRecord }

interface FolderListRowProps {
  item: FolderListItem
  selected: boolean
  isFullText: boolean
  /**
   * Thư mục ĐANG XEM — nguồn của lượt kéo khi thả dòng này ra ngoài. `null` =
   * không gắn với một thư mục cụ thể (gốc «Thư mục của bạn» — xem
   * `folder-child-cards.tsx`).
   */
  sourceFolderId: number | null
  onClick: (modifiers: SelectionModifierKeys) => void
  onOpen: () => void
  onViewDetails: () => void
  onRename?: () => void
  onMoveTo?: () => void
  onManagePermissions?: () => void
  onRemove?: () => void
  canWriteDocument?: boolean
  canDeleteDocument?: boolean
  /** Chỉ có nghĩa với dòng THƯ MỤC — đang là đích thả hợp lệ (tô nền). */
  dropHighlighted?: boolean
  onDragOverFolder?: () => void
  onDragLeaveFolder?: () => void
  onDropOnFolder?: (payload: FolderDragPayload, keepInSource: boolean) => void
  /** `false` = không vẽ ô tick đầu dòng (gốc «Thư mục của bạn»). Mặc định `true`. */
  selectable?: boolean
}

/**
 * MỘT DÒNG của danh sách kiểu Drive (`folder-list-view.tsx`, đặc tả §B, phản
 * hồi 24/09/2026 — chốt dọn gọn tối 24/09: BỎ hẳn ô tick, "Drive selection
 * model" ở đây chỉ còn TÔ NỀN dòng đang chọn (`bg-accent`), không có biểu
 * tượng nào khác đứng chồng lên icon) — dùng CHUNG cho thư mục con lẫn văn
 * bản, cao 48px (`h-12`). Menu `⋯` + (thư mục) nút «Chia sẻ» nổi ở mép phải
 * qua `FolderItemContextMenu`.
 *
 * Bấm MỘT LẦN = mở; ô tick đầu dòng hoặc Ctrl/⌘/Shift+bấm = chọn
 * (`dispatchFolderItemClick`, chốt 24/09/2026 — bỏ bấm đúp).
 */
export function FolderListRow({
  item,
  selected,
  isFullText,
  sourceFolderId,
  onClick,
  onOpen,
  onViewDetails,
  onRename,
  onMoveTo,
  onManagePermissions,
  onRemove,
  canWriteDocument,
  canDeleteDocument,
  dropHighlighted,
  onDragOverFolder,
  onDragLeaveFolder,
  onDropOnFolder,
  selectable = true,
}: FolderListRowProps) {
  const isFolder = item.kind === 'folder'
  const domId = isFolder ? undefined : folderItemDomId('document', item.document.id)
  const dragPayload: FolderDragPayload = isFolder
    ? { documentIds: [], folderIds: [item.folder.id], sourceFolderId }
    : { documentIds: [item.document.id], folderIds: [], sourceFolderId }
  const rowLabel = isFolder ? (item.folder.display_name ?? item.folder.name) : item.document.title

  return (
    <FolderItemContextMenu
      kind={item.kind}
      myLevel={isFolder ? item.folder.my_level : undefined}
      isCompanyRoot={isFolder ? item.folder.kind === FOLDER_KIND.company : undefined}
      canWriteDocument={canWriteDocument}
      canDeleteDocument={canDeleteDocument}
      showMenuButton
      onOpen={onOpen}
      onRename={onRename}
      onMoveTo={onMoveTo}
      onManagePermissions={onManagePermissions}
      onViewDetails={onViewDetails}
      onRemove={onRemove}
      removeDisabledReason={isFolder ? folderDeleteDisabledReason(item.folder) : undefined}
    >
      <div
        id={domId}
        role="button"
        tabIndex={0}
        aria-label={rowLabel}
        data-selected={selected}
        aria-pressed={selected}
        draggable
        onDragStart={(event) => writeFolderDragPayload(event.dataTransfer, dragPayload)}
        onDragOver={(event) => {
          if (!isFolder || !hasFolderDragPayload(event.dataTransfer)) return
          event.preventDefault()
          onDragOverFolder?.()
        }}
        onDragLeave={() => isFolder && onDragLeaveFolder?.()}
        onDrop={(event) => {
          if (!isFolder) return
          event.preventDefault()
          const payload = readFolderDragPayload(event.dataTransfer)
          if (payload) onDropOnFolder?.(payload, event.altKey)
        }}
        onClick={(event) =>
          dispatchFolderItemClick(readModifierKeys(event), { onSelect: onClick, onOpen })
        }
        onKeyDown={(event) => {
          if (event.key === 'Enter') onOpen()
        }}
        className={cn(
          selectable ? FOLDER_LIST_GRID_TEMPLATE : FOLDER_LIST_GRID_TEMPLATE_NO_SELECT,
          'h-12 cursor-pointer px-3 text-sm hover:bg-accent/60',
          selected && 'bg-accent',
          dropHighlighted && 'bg-emerald-50 ring-2 ring-emerald-400 ring-inset',
        )}
      >
        {selectable &&
          (!isFolder || canBulkSelectFolder(item.folder) ? (
            <FolderItemSelectCheckbox
              checked={selected}
              onToggle={() => onClick({ ctrlKey: true })}
              label={`Chọn ${rowLabel}`}
            />
          ) : (
            //  Giữ ô trống để cột Tên không lệch so với các dòng có ô tick.
            <span aria-hidden />
          ))}

        <NameCell item={item} isFullText={isFullText} />

        {isFolder ? (
          <Cell dash className={FOLDER_LIST_OWNER_COLUMN} />
        ) : (
          <span
            className={cn(
              FOLDER_LIST_OWNER_COLUMN,
              'min-w-0 items-center gap-1.5 text-muted-foreground',
            )}
          >
            <Avatar size="sm" className="shrink-0">
              <AvatarFallback className="text-[10px]">
                {nameInitials(item.document.drafter_name || item.document.owner_name || '?')}
              </AvatarFallback>
            </Avatar>
            <span className="truncate">
              {item.document.drafter_name || item.document.owner_name || '—'}
            </span>
          </span>
        )}

        {isFolder ? (
          <Cell dash />
        ) : (
          <span className="truncate text-muted-foreground">
            {formatDate(item.document.created_at)}
          </span>
        )}

        {isFolder ? <Cell dash /> : <span>{effectiveStatusBadge(item.document)}</span>}

        {/*  Văn bản chỉ có nút này khi được chia quyền (`onManagePermissions`
             chỉ truyền khi có `write`); thư mục thì luôn có, hộp tự chuyển chỉ-đọc. */}
        {(isFolder || onManagePermissions) && (
          <IconTooltip label="Chia sẻ">
            <button
              type="button"
              aria-label={`Chia sẻ ${rowLabel}`}
              onClick={(event) => {
                event.stopPropagation()
                onManagePermissions?.()
              }}
              className="flex size-6 shrink-0 items-center justify-center rounded opacity-0 transition-opacity group-hover/pill:opacity-100 hover:bg-muted focus-visible:opacity-100"
            >
              <Share2 className="size-3.5" />
            </button>
          </IconTooltip>
        )}
      </div>
    </FolderItemContextMenu>
  )
}
