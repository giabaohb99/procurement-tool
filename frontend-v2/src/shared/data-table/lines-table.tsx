import { Columns3 } from 'lucide-react'
import { useCallback, useMemo, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'

import { Button } from '@/shared/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { columnColorStyle } from './column-color-palette'
import { ColumnHeaderCell } from './column-header-cell'
import { ColumnVisibilityMenu } from './column-visibility-menu'
import { measureColumnContentWidth } from './measure-column-width'
import { columnLabel } from './required-header'
import type { DataTableColumn, LinesTableColumn } from './types'
import { useColumnDrag } from './use-column-drag'
import { usePinnedOffsets } from './use-pinned-offsets'
import { useTableLayout } from './use-table-layout'

const DEFAULT_MIN_WIDTH = 40

/**
 * ⚠️ Viền ô tiêu đề vẽ bằng `box-shadow`, KHÔNG dùng `border` — giống `DataTable`.
 * Tailwind preflight đặt `border-collapse: collapse`, ở chế độ đó viền thuộc về
 * bảng chứ không thuộc ô, nên `<thead>` dính đỉnh là mất sạch đường kẻ.
 */
const HEAD_CELL =
  'relative h-10 px-2.5 text-[13px] font-bold text-slate-900 dark:text-slate-100 bg-slate-200/80 dark:bg-slate-800/90 shadow-[inset_-1px_0_0_0_var(--border),inset_0_-1px_0_0_var(--border)] last:shadow-[inset_0_-1px_0_0_var(--border)]'
const BODY_CELL = 'border-r px-2.5 py-1.5 align-middle last:border-r-0 text-[13.5px] text-foreground'
/**
 * Nền hàng xen kẽ sọc đậm/nhạt rõ nét (zebra striping: odd bg-card, even bg-slate-100).
 * Ô của cột ghim lấy `bg-inherit` từ hàng nên tự động thừa hưởng màu sọc tương ứng.
 */
const ROW_BG = 'group odd:bg-card even:bg-slate-100 dark:even:bg-slate-800/60 hover:bg-sky-100/70 dark:hover:bg-slate-800 transition-colors'

export interface LinesTableProps<T> {
  columns: LinesTableColumn[]
  rows: T[]
  /** Khóa nhớ bố cục cột trong localStorage (`erp.table.<key>`). */
  storageKey: string
  /** Khóa React của hàng — dòng chưa lưu chưa có id nên cần cả chỉ số. */
  rowKey: (row: T, index: number) => string | number
  /** Vẽ nội dung một ô. `key` là khóa cột, `index` là vị trí dòng trong mảng. */
  renderCell: (columnKey: string, row: T, index: number) => ReactNode
  /** Tiêu đề bên trái thanh công cụ. */
  title: ReactNode
  /** Nút riêng của từng bảng (Thêm dòng, Thêm nhiều…), đặt cạnh tiêu đề. */
  actions?: ReactNode
  emptyMessage: ReactNode
  /**
   * Lần đầu mở bảng thì ẩn sẵn nhóm cột phụ (`compactHidden`). Dành cho bảng
   * quá nhiều cột — mở ra là một rừng chữ, người dùng bấm "Bảng đầy đủ" khi cần.
   * Chỉ là MẶC ĐỊNH: bố cục người dùng đã chỉnh vẫn được nhớ như thường.
   */
  defaultCompact?: boolean
  rowClassName?: (row: T, index: number) => string | undefined
  cellClassName?: (columnKey: string, row: T, index: number) => string | undefined
}

/**
 * Bảng DÒNG CHỨNG TỪ dùng chung: ẩn/hiện cột, ghim cột, kéo thả đổi thứ tự, kéo
 * giãn, tô màu cột, nhớ vào localStorage — đúng bộ đồ nghề của `DataTable` nhưng
 * cho bảng SỬA ĐƯỢC (ô chứa input/select, nội dung vẽ theo chỉ số dòng).
 *
 * Thêm nút "Bảng rút gọn / Bảng đầy đủ": bung ra là hiện hết nhóm cột phụ
 * (`compactHidden`), thu lại thì chỉ còn các cột xương sống.
 *
 * ⚠️ KHÔNG đặt bề rộng cứng cho `<table>`. `table-fixed` + `w-full` cho bề rộng
 * bằng max(khung chứa, tổng bề rộng cột): ẩn bớt cột thì bảng vẫn phủ kín khung,
 * mở nhiều cột thì tự cuộn ngang. Đặt `width: tổng cột` là ẩn cột xong bảng co
 * lại, chừa một khoảng trắng bên phải trong khung viền.
 */
export function LinesTable<T>({
  columns,
  rows,
  storageKey,
  rowKey,
  renderCell,
  title,
  actions,
  emptyMessage,
  defaultCompact,
  rowClassName,
  cellClassName,
}: LinesTableProps<T>) {
  /**
   * `useTableLayout` nhận cột của bảng danh sách; bảng dòng không khai `cell` nên
   * bù vào một hàm rỗng. Nội dung ô do `renderCell` vẽ.
   */
  const layoutColumns = useMemo<DataTableColumn<T>[]>(
    () =>
      columns.map((column) => ({
        ...column,
        cell: () => null,
        defaultHidden: defaultCompact && column.compactHidden,
      })),
    [columns, defaultCompact],
  )

  const {
    layout,
    orderedColumns,
    visibleColumns,
    toggleColumn,
    setHiddenColumns,
    setColumnWidth,
    setColumnWidths,
    setColumnColor,
    moveColumn,
    togglePin,
    resetLayout,
  } = useTableLayout(layoutColumns, storageKey)

  const { drag, startDrag } = useColumnDrag(moveColumn)
  const tableRef = useRef<HTMLTableElement>(null)

  /** Cột ghim theo đúng thứ tự đang hiện — chúng luôn là dải đầu bảng. */
  const pinnedKeys = useMemo(() => {
    const keys: string[] = []
    for (const column of visibleColumns) {
      if (!layout.pinnedColumns.includes(column.key)) break
      keys.push(column.key)
    }
    return keys
  }, [visibleColumns, layout.pinnedColumns])

  const { headerRowRef, pinnedOffsets, scrolledX } = usePinnedOffsets(pinnedKeys)
  const lastPinnedKey = pinnedKeys.at(-1)

  const compactKeys = useMemo(
    () => columns.filter((column) => column.compactHidden).map((column) => column.key),
    [columns],
  )
  const isCompact =
    compactKeys.length > 0 && compactKeys.every((key) => layout.hiddenColumns.includes(key))

  function toggleCompactMode() {
    if (isCompact) {
      setHiddenColumns((prev) => prev.filter((key) => !compactKeys.includes(key)))
    } else {
      setHiddenColumns((prev) => Array.from(new Set([...prev, ...compactKeys])))
    }
  }

  const autoFitAll = useCallback(() => {
    const table = tableRef.current
    if (!table) return

    const widths: Record<string, number> = {}
    visibleColumns.forEach((column, index) => {
      widths[column.key] = measureColumnContentWidth(table, index, {
        min: column.minWidth ?? DEFAULT_MIN_WIDTH,
      })
    })
    setColumnWidths(widths)
  }, [visibleColumns, setColumnWidths])

  const widthOf = (column: DataTableColumn<T>) =>
    layout.columnWidths[column.key] ?? column.width

  /**
   * Ô thuộc cột ghim: nền `bg-inherit` ăn theo hàng, tự vẽ vạch bằng `inset
   * shadow` (ô dính nằm đè lên ô kế bên, để cả hai cùng `border-r` là vạch đôi).
   */
  const pinClass = (key: string) =>
    pinnedKeys.includes(key) &&
    cn(
      'sticky z-20 border-r-0 bg-inherit',
      'shadow-[inset_-1px_0_0_0_var(--border)]',
      key === lastPinnedKey &&
        scrolledX &&
        'shadow-[inset_-1px_0_0_0_var(--border),6px_0_8px_-6px_rgb(0_0_0/0.18)]',
    )

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-semibold text-foreground">{title}</span>
          {actions}
        </div>

        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={toggleCompactMode}
            disabled={compactKeys.length === 0}
            title="Chuyển chế độ xem rút gọn / đầy đủ"
          >
            <Columns3 />
            {isCompact ? 'Bảng đầy đủ' : 'Bảng rút gọn'}
          </Button>

          <ColumnVisibilityMenu
            columns={orderedColumns}
            hiddenColumns={layout.hiddenColumns}
            pinnedColumns={layout.pinnedColumns}
            columnColors={layout.columnColors}
            onToggle={toggleColumn}
            onTogglePin={togglePin}
            onAutoFitAll={autoFitAll}
            onColorChange={setColumnColor}
            onMove={moveColumn}
            onReset={resetLayout}
          />
        </div>
      </div>

      {/*
        `isolate` tạo ngữ cảnh xếp lớp riêng: `z-index` của cột ghim chỉ so với
        nhau, không trồi lên trên thanh tiêu đề của trang khi cuộn.
      */}
      <div className="isolate overflow-hidden rounded-lg border">
        <Table ref={tableRef} className="table-fixed">
          <TableHeader className="bg-muted">
            {/*
              `hover:bg-muted` không thừa: `TableRow` mặc định có `hover:bg-muted/50`
              — nền alpha ở hàng tiêu đề là ô cột ghim `bg-inherit` lộ hàng bên dưới.
            */}
            <TableRow ref={headerRowRef} className="bg-muted hover:bg-muted">
              {visibleColumns.map((column) => (
                <ColumnHeaderCell
                  key={column.key}
                  column={column}
                  width={widthOf(column)}
                  minWidth={column.minWidth ?? DEFAULT_MIN_WIDTH}
                  className={cn(
                    HEAD_CELL,
                    alignClass(column.align),
                    pinClass(column.key),
                  )}
                  colorStyle={columnColorStyle(layout.columnColors[column.key], 'head')}
                  pinnedOffset={pinnedOffsets[column.key]}
                  dragging={drag?.fromKey === column.key}
                  dropSide={drag?.overKey === column.key ? drag.side : null}
                  onResize={(next) => setColumnWidth(column.key, next)}
                  onDragStart={(event) => startDrag(event, column.key, columnLabel(column.header))}
                />
              ))}
            </TableRow>
          </TableHeader>

          <TableBody>
            {rows.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={visibleColumns.length}
                  className="h-20 px-3 text-center text-muted-foreground"
                >
                  {emptyMessage}
                </TableCell>
              </TableRow>
            )}

            {rows.map((row, index) => (
              <TableRow
                key={rowKey(row, index)}
                className={cn(ROW_BG, rowClassName?.(row, index))}
              >
                {visibleColumns.map((column) => (
                  <TableCell
                    key={column.key}
                    style={{
                      width: widthOf(column),
                      left: pinnedOffsets[column.key],
                      // Màu cột đặt SAU nền hàng: ô đã tô giữ nguyên màu kể cả
                      // khi rê chuột, đúng ý "đánh dấu cột".
                      ...columnColorStyle(layout.columnColors[column.key], 'cell'),
                    }}
                    className={cn(
                      BODY_CELL,
                      alignClass(column.align),
                      cellClassName?.(column.key, row, index),
                      pinClass(column.key),
                    )}
                  >
                    <div
                      className={cn(
                        column.wrap === false
                          ? 'truncate'
                          : 'break-words whitespace-normal leading-snug',
                      )}
                    >
                      {(() => {
                        const content = renderCell(column.key, row, index)
                        return typeof content === 'string' && (content === '—' || content === '-')
                          ? ''
                          : content
                      })()}
                    </div>
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Nhãn bám con trỏ khi kéo cột — vẽ vào `body` để không bị khung viền
          `overflow-hidden` của bảng cắt mất. */}
      {drag &&
        createPortal(
          <div
            style={{ left: drag.x + 12, top: drag.y + 12 }}
            className="pointer-events-none fixed z-50 rounded-md border bg-popover px-2.5 py-1 text-xs font-medium text-popover-foreground shadow-lg"
          >
            {drag.label}
          </div>,
          document.body,
        )}
    </div>
  )
}

function alignClass(align: LinesTableColumn['align']) {
  if (align === 'right') return 'text-right'
  if (align === 'center') return 'text-center'
  return undefined
}
