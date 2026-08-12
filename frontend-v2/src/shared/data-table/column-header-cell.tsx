import { useState, type PointerEvent as ReactPointerEvent } from 'react'

import { TableHead } from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { ColumnResizeHandle } from './column-resize-handle'
import type { ColumnDropSide, DataTableColumn } from './types'

interface ColumnHeaderCellProps<T> {
  column: DataTableColumn<T>
  width?: number
  className?: string
  minWidth: number
  /** Ô này đang được kéo đi. */
  dragging?: boolean
  /** Cột kéo sẽ chèn vào trước/sau ô này; `null` = không phải đích đang trỏ. */
  dropSide?: ColumnDropSide | null
  /** Cột đang ghim: khoảng cách dính tính từ mép trái bảng. */
  pinnedOffset?: number
  onResize: (width: number) => void
  onDragStart: (event: ReactPointerEvent<HTMLTableCellElement>) => void
}

/**
 * Ô tiêu đề: nhãn cột + bắt đầu kéo đổi vị trí + vạch kéo giãn ở mép phải.
 *
 * Trạng thái kéo do `useColumnDrag` ở `DataTable` giữ (cần biết cả hàng để tính
 * ô nào đang bị trỏ tới), ô này chỉ nhận kết quả về để vẽ.
 */
export function ColumnHeaderCell<T>({
  column,
  width,
  className,
  minWidth,
  dragging,
  dropSide,
  pinnedOffset,
  onResize,
  onDragStart,
}: ColumnHeaderCellProps<T>) {
  const [resizing, setResizing] = useState(false)

  return (
    <TableHead
      data-column-key={column.key}
      style={{ width, left: pinnedOffset }}
      className={cn(
        'select-none transition-[opacity,box-shadow] duration-150',
        resizing ? 'cursor-col-resize' : 'cursor-grab active:cursor-grabbing',
        dragging && 'opacity-40',
        // Vạch báo chỗ sắp thả. Dùng `inset shadow` cho đồng bộ với viền ô tiêu
        // đề (xem ghi chú về `border-collapse` trong `data-table.tsx`).
        dropSide === 'before' && 'shadow-[inset_2px_0_0_0_var(--primary)]',
        dropSide === 'after' && 'shadow-[inset_-2px_0_0_0_var(--primary)]',
        className,
      )}
      title={`${column.header} — kéo để đổi vị trí cột`}
      onPointerDown={onDragStart}
    >
      <span className="pointer-events-none block truncate">{column.header}</span>
      <ColumnResizeHandle
        minWidth={minWidth}
        onResize={onResize}
        onResizingChange={setResizing}
      />
    </TableHead>
  )
}
