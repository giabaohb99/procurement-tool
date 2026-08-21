import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'
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
  /** `false` với cột thao tác cố định bên phải: vẫn cho đổi độ rộng, không cho dời. */
  draggable?: boolean
  /** Cột đang ghim: khoảng cách dính tính từ mép trái bảng. */
  pinnedOffset?: number
  /** Cột thao tác cố định: khoảng cách dính tính từ mép phải bảng. */
  pinnedRightOffset?: number
  /** Bỏ vạch phải khi ô kế tiếp đã tự vẽ vạch trái (tránh hai border sát nhau). */
  suppressRightDivider?: boolean
  /** Nền của cột do người dùng tự tô (xem `column-color-palette.ts`). */
  colorStyle?: CSSProperties
  sortDir?: 'asc' | 'desc' | null
  onSort?: () => void
  onResize: (width: number) => void
  onDragStart: (event: ReactPointerEvent<HTMLTableCellElement>) => void
}

/**
 * Ô tiêu đề: nhãn cột + bắt đầu kéo đổi vị trí + nút sắp xếp + vạch kéo giãn ở mép phải.
 */
export function ColumnHeaderCell<T>({
  column,
  width,
  className,
  minWidth,
  dragging,
  dropSide,
  draggable = true,
  pinnedOffset,
  pinnedRightOffset,
  suppressRightDivider = false,
  colorStyle,
  sortDir,
  onSort,
  onResize,
  onDragStart,
}: ColumnHeaderCellProps<T>) {
  const [resizing, setResizing] = useState(false)
  const { label, required } = splitRequiredHeader(column.header)

  const isSortable = Boolean(column.sortable && onSort)

  return (
    <TableHead
      data-column-key={column.key}
      style={{
        width,
        left: pinnedOffset,
        right: pinnedRightOffset,
        ...(suppressRightDivider ? { boxShadow: 'inset 0 -1px 0 0 var(--border)' } : undefined),
        ...colorStyle,
      }}
      className={cn(
        'transition-[opacity,box-shadow] duration-150 select-none',
        resizing
          ? 'cursor-col-resize'
          : draggable
            ? 'cursor-grab active:cursor-grabbing'
            : 'cursor-default',
        dragging && 'opacity-40',
        className,
      )}
      onPointerDown={draggable ? onDragStart : undefined}
    >
      <div
        className={cn(
          'flex items-center gap-1 overflow-hidden',
          isSortable && 'cursor-pointer hover:text-foreground',
        )}
        onClick={(e) => {
          if (isSortable) {
            e.stopPropagation()
            onSort?.()
          }
        }}
      >
        <span className="truncate">
          {label}
          {required && <RequiredMark />}
        </span>

        {isSortable && (
          <span className="shrink-0 text-muted-foreground">
            {sortDir === 'asc' ? (
              <ArrowUp className="h-3.5 w-3.5 text-primary" />
            ) : sortDir === 'desc' ? (
              <ArrowDown className="h-3.5 w-3.5 text-primary" />
            ) : (
              <ArrowUpDown className="h-3.5 w-3.5 opacity-40 hover:opacity-100" />
            )}
          </span>
        )}
      </div>

      {dropSide && <ColumnDropIndicator side={dropSide} />}
      <ColumnResizeHandle minWidth={minWidth} onResize={onResize} onResizingChange={setResizing} />
    </TableHead>
  )
}
