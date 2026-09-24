import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import type { DocumentSortField, SortDirection } from '../helpers/sort-document-rows'

interface FolderSortButtonProps {
  label: string
  field: DocumentSortField
  activeField: DocumentSortField
  dir: SortDirection
  onSortFieldChange: (field: DocumentSortField) => void
  onToggleSortDir: () => void
  className?: string
}

/**
 * MỘT nhãn sắp xếp bấm được kiểu Drive ("Tên ↑") — dùng CHUNG cho tiêu đề cột
 * của Danh sách (`folder-list-view.tsx`) và dải nhãn nhỏ phía trên Lưới
 * (`folder-documents-view.tsx`), thay Select + nút đổi chiều rời rạc trước đó
 * (đặc tả A, phản hồi 24/09/2026). Bấm đúng cột đang sắp xếp → ĐỔI CHIỀU; bấm
 * cột khác → chuyển sắp xếp sang cột đó (giữ nguyên chiều hiện tại, cùng hành
 * vi Select cũ).
 */
export function FolderSortButton({
  label,
  field,
  activeField,
  dir,
  onSortFieldChange,
  onToggleSortDir,
  className,
}: FolderSortButtonProps) {
  const active = field === activeField

  return (
    <button
      type="button"
      onClick={() => (active ? onToggleSortDir() : onSortFieldChange(field))}
      aria-label={`Sắp xếp theo ${label}${active ? (dir === 'asc' ? ' — đang tăng dần' : ' — đang giảm dần') : ''}`}
      className={cn(
        'inline-flex items-center gap-1 hover:text-foreground',
        active ? 'font-medium text-foreground' : 'text-muted-foreground',
        className,
      )}
    >
      {label}
      {active ? (
        dir === 'asc' ? (
          <ArrowUp className="size-3.5 text-primary" />
        ) : (
          <ArrowDown className="size-3.5 text-primary" />
        )
      ) : (
        <ArrowUpDown className="size-3.5 opacity-40" />
      )}
    </button>
  )
}
