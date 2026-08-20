import { useState, type CSSProperties, type PointerEvent as ReactPointerEvent } from 'react'

import { RequiredMark } from '@/shared/ui/required-mark'
import { TableHead } from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { ColumnDropIndicator } from './column-drop-indicator'
import { ColumnResizeHandle } from './column-resize-handle'
import { splitRequiredHeader } from './required-header'
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
  /** Nền của cột do người dùng tự tô (xem `column-color-palette.ts`). */
  colorStyle?: CSSProperties
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
  colorStyle,
  onResize,
  onDragStart,
}: ColumnHeaderCellProps<T>) {
  const [resizing, setResizing] = useState(false)
  const { label, required } = splitRequiredHeader(column.header)

  return (
    <TableHead
      data-column-key={column.key}
      style={{ width, left: pinnedOffset, ...colorStyle }}
      className={cn(
        'select-none transition-[opacity,box-shadow] duration-150',
        resizing ? 'cursor-col-resize' : 'cursor-grab active:cursor-grabbing',
        dragging && 'opacity-40',
        className,
      )}
      onPointerDown={onDragStart}
    >
      <span className="pointer-events-none block truncate">
        {label}
        {required && <RequiredMark />}
      </span>
      {dropSide && <ColumnDropIndicator side={dropSide} />}
      <ColumnResizeHandle
        minWidth={minWidth}
        onResize={onResize}
        onResizingChange={setResizing}
      />
    </TableHead>
  )
}
