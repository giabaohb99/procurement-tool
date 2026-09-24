import { effectiveLabel } from './document-status'
import type { DocumentRecord } from '../types/document-record'

/**
 * Màu icon văn bản THEO TRẠNG THÁI HIỆU LỰC — dùng CHUNG cho thẻ Lưới
 * (`folder-grid-document-card.tsx`) và dòng Danh sách kiểu Drive
 * (`folder-list-view.tsx`), tách ra khỏi thẻ Lưới (phase 10, duoc-CR-476) để
 * một văn bản luôn ra ĐÚNG một tông màu dù đang xem ở chế độ nào — trước đây
 * mỗi nơi tự khai một bảng màu riêng (cây bên trái còn một bảng THỨ BA,
 * `STATUS_ICON_COLOR` của `folder-tree-document-leaf-item.tsx`, cố ý giữ khác
 * vì đó là ngữ cảnh dòng CÂY chứ không phải thẻ/dòng nội dung).
 */
const DOCUMENT_ICON_TINT: Record<ReturnType<typeof effectiveLabel>['variant'], string> = {
  default: 'text-primary',
  secondary: 'text-muted-foreground',
  outline: 'text-amber-600 dark:text-amber-500',
  destructive: 'text-destructive',
}

export function documentIconTint(document: Pick<DocumentRecord, 'status' | 'effective_date' | 'expire_date'>): string {
  return DOCUMENT_ICON_TINT[effectiveLabel(document).variant]
}
