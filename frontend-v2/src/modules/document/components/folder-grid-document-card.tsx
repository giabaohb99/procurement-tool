import { FileText } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { documentIconTint } from '../helpers/document-icon-tint'
import { dispatchFolderItemClick, readModifierKeys } from '../helpers/folder-item-click'
import { folderItemDomId } from '../helpers/folder-item-id'
import { FolderItemSelectCheckbox } from './folder-item-select-checkbox'
import { docCodeText, effectiveStatusBadge } from './outgoing-document-columns'
import type { SelectionModifierKeys } from '../hooks/use-item-selection'
import type { DocumentRecord } from '../types/document-record'

interface FolderGridDocumentCardProps {
  document: DocumentRecord
  selected: boolean
  onClick: (modifiers: SelectionModifierKeys) => void
  onOpen: () => void
}

/**
 * THẺ VĂN BẢN của chế độ Lưới (đặc tả §P4, làm lại UI 23/09/2026) — vùng xem
 * trước `bg-muted` + icon lớn tô theo trạng thái, rồi icon nhỏ + tiêu đề MỘT
 * DÒNG (cắt bằng «…»), dòng thứ hai «số hiệu · huy hiệu trạng thái». Ngày tạo
 * chỉ còn trong `title` (tooltip nguyên bản trình duyệt) — trước đây một hàng
 * ngang «huy hiệu · ngày» tràn ra ngoài card khi huy hiệu dài (bug lead bắt
 * 23/09/2026: "card footers overflow — dates spill outside").
 *
 * Bấm MỘT LẦN = mở (chốt 24/09/2026, bỏ bấm đúp); Ctrl/⌘/Shift+bấm hoặc
 * bấm ô tick = chọn (qua {@link onClick}). Ô tick LUÔN hiện ở góc (chốt
 * 24/09/2026 — bản ẩn-tới-khi-rê-chuột thì người dùng không biết có chỗ chọn).
 */
export function FolderGridDocumentCard({
  document,
  selected,
  onClick,
  onOpen,
}: FolderGridDocumentCardProps) {
  const iconTint = documentIconTint(document)

  return (
    <div
      id={folderItemDomId('document', document.id)}
      role="button"
      tabIndex={0}
      aria-label={document.title}
      data-selected={selected}
      aria-pressed={selected}
      onClick={(event) =>
        dispatchFolderItemClick(readModifierKeys(event), { onSelect: onClick, onOpen })
      }
      onKeyDown={(event) => {
        if (event.key === 'Enter') onOpen()
      }}
      title={`${document.title} — ${formatDate(document.created_at)}`}
      className={cn(
        'group relative flex cursor-pointer flex-col overflow-hidden rounded-lg border text-left transition-colors hover:bg-accent/60',
        selected && 'border-primary bg-accent ring-1 ring-primary',
      )}
    >
      <FolderItemSelectCheckbox
        checked={selected}
        onToggle={() => onClick({ ctrlKey: true })}
        label={`Chọn văn bản ${document.title}`}
        className="absolute top-1.5 left-1.5 z-10 rounded bg-background/90 p-0.5 shadow-sm"
      />

      <div className="flex h-20 shrink-0 items-center justify-center bg-muted">
        <FileText className={cn('size-9', iconTint)} />
      </div>

      <div className="min-w-0 space-y-1 p-2.5">
        <div className="flex min-w-0 items-center gap-1.5">
          <FileText className={cn('size-3.5 shrink-0', iconTint)} />
          <p className="min-w-0 flex-1 truncate text-sm font-medium">{document.title}</p>
        </div>
        <div className="flex min-w-0 items-center gap-1.5 pl-5 text-xs text-muted-foreground">
          <span className="min-w-0 flex-1 truncate">{docCodeText(document)}</span>
          <span className="shrink-0">{effectiveStatusBadge(document)}</span>
        </div>
      </div>
    </div>
  )
}
