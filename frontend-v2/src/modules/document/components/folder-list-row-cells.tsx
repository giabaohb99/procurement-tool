import { FileText } from 'lucide-react'

import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import { nameInitials } from '@/shared/utils/name-initials'
import { FOLDER_STATUS } from '../types/document-folder'
import { documentIconTint } from '../helpers/document-icon-tint'
import type { DocumentSearchResult } from '../types/document-search'
import type { FolderListItem } from './folder-list-row'
import { FolderNodeIcon } from './folder-tree-item'
import { SearchSnippet } from './search-snippet'

/** Tách khỏi `folder-list-row.tsx` để tệp đó dưới 200 dòng — hai ô con dùng CHUNG cho mọi dòng (thư mục lẫn văn bản) của `folder-list-view.tsx`. */

/** Ô «—» khi không có giá trị để hiện. */
export function Cell({ dash, className }: { dash: boolean; className?: string }) {
  return dash ? <span className={cn('text-muted-foreground', className)}>—</span> : null
}

/** Cột «Người soạn» — avatar chữ viết tắt + tên; dùng chung cho văn bản (người soạn) và thư mục (người tạo). */
export function PersonCell({ name, className }: { name: string; className?: string }) {
  if (!name) return <Cell dash className={className} />
  return (
    <span className={cn('min-w-0 items-center gap-1.5 text-muted-foreground', className)}>
      <Avatar size="sm" className="shrink-0">
        <AvatarFallback className="text-[10px]">{nameInitials(name)}</AvatarFallback>
      </Avatar>
      <span className="truncate">{name}</span>
    </span>
  )
}

/** Cột «Trạng thái» của dòng THƯ MỤC — Đang dùng / Ngừng dùng. */
export function FolderStatusCell({ status, label }: { status: number; label: string }) {
  if (!label) return <Cell dash />
  return (
    <span>
      <Badge variant={status === FOLDER_STATUS.archived ? 'secondary' : 'outline'} className="font-normal">
        {label}
      </Badge>
    </span>
  )
}

/** Cột Tên — icon + tên, kèm đoạn khớp tìm toàn văn (chỉ văn bản, khi `isFullText`). */
export function NameCell({ item, isFullText }: { item: FolderListItem; isFullText: boolean }) {
  if (item.kind === 'folder') {
    return (
      <span className="flex min-w-0 items-center gap-2">
        <FolderNodeIcon data={item.folder} />
        <span className="truncate font-medium">{item.folder.display_name ?? item.folder.name}</span>
      </span>
    )
  }
  const iconTint = documentIconTint(item.document)
  return (
    <span className="flex min-w-0 flex-col justify-center">
      <span className="flex min-w-0 items-center gap-2">
        <FileText className={cn('size-4 shrink-0', iconTint)} />
        <span className="truncate font-medium">{item.document.title}</span>
      </span>
      {isFullText && <SearchSnippet hit={(item.document as DocumentSearchResult).search} className="pl-7" />}
    </span>
  )
}
