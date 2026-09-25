import { FileText } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import { documentIconTint } from '../helpers/document-icon-tint'
import type { DocumentSearchResult } from '../types/document-search'
import type { FolderListItem } from './folder-list-row'
import { FolderNodeIcon } from './folder-tree-item'
import { SearchSnippet } from './search-snippet'

/** Tách khỏi `folder-list-row.tsx` để tệp đó dưới 200 dòng — hai ô con dùng CHUNG cho mọi dòng (thư mục lẫn văn bản) của `folder-list-view.tsx`. */

/** Ô «—» cho cột chỉ có nghĩa với văn bản (Người soạn/Ngày tạo/Trạng thái) khi dòng là THƯ MỤC. */
export function Cell({ dash, className }: { dash: boolean; className?: string }) {
  return dash ? <span className={cn('text-muted-foreground', className)}>—</span> : null
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
