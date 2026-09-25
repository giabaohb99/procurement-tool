import { FileText, Loader2 } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import type { FolderTreeLeafData } from '../helpers/insert-folder-document-leaves'
import { STATUS_VARIANTS } from '../types/document-record'

/** Màu icon văn bản THEO TRẠNG THÁI — dùng lại đúng phân loại `STATUS_VARIANTS`
 * của huy hiệu trạng thái (`document-status.ts`) để một văn bản luôn ra CÙNG
 * một tông màu dù đang xem ở cây, ở lưới hay ở bảng. */
const STATUS_ICON_COLOR: Record<string, string> = {
  default: 'text-sky-600 dark:text-sky-400',
  secondary: 'text-muted-foreground',
  outline: 'text-muted-foreground',
  destructive: 'text-destructive',
}

/**
 * Icon của MỘT DÒNG LÁ chèn thêm dưới thư mục — văn bản trực tiếp / «(trống)»
 * / «đang tải…» / «Xem thêm…» (bốn loại, xem `insert-folder-document-leaves.ts`).
 * Tách khỏi `folder-tree-item.tsx` (chỉ lo icon THƯ MỤC) để cả hai tệp giữ
 * dưới 200 dòng.
 */
export function FolderTreeLeafIcon({ leaf }: { leaf: FolderTreeLeafData }) {
  if (leaf.type === 'loading') {
    return <Loader2 className="size-4 shrink-0 animate-spin text-muted-foreground" aria-hidden />
  }
  if (leaf.type === 'document') {
    const variant = STATUS_VARIANTS[leaf.document.status] ?? 'secondary'
    return <FileText className={cn('size-4 shrink-0', STATUS_ICON_COLOR[variant])} aria-hidden />
  }
  //  'empty' | 'more': không icon riêng — vẫn chừa đúng chỗ (size-4) để nhãn
  //  thẳng hàng với các dòng có icon bên cạnh.
  return <span className="size-4 shrink-0" aria-hidden />
}

/**
 * Nhãn dòng lá — văn bản hiện TIÊU ĐỀ như một dòng thường; «Xem thêm…» tô màu
 * NHƯ LIÊN KẾT (mời bấm); «(trống)»/«đang tải…» chữ mờ nghiêng kiểu chú thích
 * (đúng ý VS Code Explorer: dòng «No matching results» trong panel rỗng).
 */
export function FolderTreeLeafLabel({ leaf, label }: { leaf: FolderTreeLeafData; label: string }) {
  if (leaf.type === 'document') {
    return <span className="min-w-0 flex-1 truncate">{label}</span>
  }
  if (leaf.type === 'more') {
    return <span className="min-w-0 flex-1 truncate text-primary">{label}</span>
  }
  return <span className="min-w-0 flex-1 truncate text-muted-foreground italic">{label}</span>
}
