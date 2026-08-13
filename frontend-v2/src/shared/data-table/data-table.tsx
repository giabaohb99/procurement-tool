import { useCallback, useMemo, useRef, type ReactNode } from 'react'

import { Skeleton } from '@/shared/ui/skeleton'
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
import { DataTablePagination } from './data-table-pagination'
import { measureColumnContentWidth } from './measure-column-width'
import type { DataTableColumn, DataTablePagination as PaginationConfig } from './types'
import { useColumnDrag } from './use-column-drag'
import { usePinnedOffsets } from './use-pinned-offsets'
import { useTableLayout } from './use-table-layout'

const DEFAULT_MIN_WIDTH = 64

/**
 * Lớp sơn đè lên `Table` mặc định của shadcn. Để ở đây (không sửa
 * `shared/ui/table.tsx`) vì đó là primitive dùng chung — sửa gốc là đổi luôn
 * mọi bảng khác.
 *
 * Mục tiêu: kẻ ô đầy đủ và MỌI dòng cùng một chiều cao. Chiều cao ô đặt cứng
 * (`h-*`) kèm `py-0` thay vì dùng padding dọc: nội dung mỗi cột một kiểu (chữ
 * thường, huy hiệu, ảnh đại diện) nên để padding tự tính thì dòng nào có huy
 * hiệu sẽ cao hơn hẳn dòng chỉ có chữ.
 */
/**
 * ⚠️ Viền của ô tiêu đề vẽ bằng `box-shadow` chứ KHÔNG dùng `border`.
 * Tailwind preflight đặt `border-collapse: collapse` cho mọi bảng; ở chế độ đó
 * viền thuộc về bảng chứ không thuộc ô, nên khi `<thead>` được `position:
 * sticky` thì trình duyệt bỏ luôn viền của nó — hàng tiêu đề trôi lơ lửng
 * không còn đường kẻ nào. `inset shadow` nằm ngoài cơ chế collapse nên vẫn hiện.
 */
const HEAD_CELL =
  'relative h-9 px-3 text-xs shadow-[inset_-1px_0_0_0_var(--border),inset_0_-1px_0_0_var(--border)] last:shadow-[inset_0_-1px_0_0_var(--border)]'
const BODY_CELL = 'h-10 overflow-hidden border-r px-3 py-0 last:border-r-0'
/**
 * Nền hàng phải là màu ĐỤC (không dùng biến thể alpha kiểu `bg-muted/50`): ô của
 * cột ghim lấy `bg-inherit` từ hàng để che phần bảng đang cuộn ngang phía dưới.
 */
const ROW_BG = 'bg-card hover:bg-muted data-[state=selected]:bg-muted'
/** Ô báo trạng thái (đang tải / lỗi / rỗng) trải hết bảng — không kẻ dọc, cao hơn. */
const SPAN_CELL = 'h-20 px-3 text-center'

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  rows: T[] | undefined
  getRowId: (row: T) => string | number

  isLoading?: boolean
  isError?: boolean
  emptyMessage?: string
  errorMessage?: string

  onRowClick?: (row: T) => void
  /** Nội dung chèn bên TRÁI menu "Cột" (ô tìm kiếm, select, nút Bộ lọc…). */
  toolbar?: ReactNode
  /** Có thì bảng nhớ cột ẩn + độ rộng + thứ tự cột vào localStorage theo khóa này. */
  storageKey?: string
  pagination?: PaginationConfig
  /**
   * Bảng cao bằng khung chứa: thanh công cụ và phân trang đứng yên, chỉ phần
   * dòng dữ liệu cuộn. Cần cha là flex column có chiều cao xác định — dùng kèm
   * `<PageContainer fill>`.
   */
  fillHeight?: boolean
}

/**
 * Bảng danh sách dùng chung cho mọi màn: ẩn/hiện cột, kéo giãn cột, kéo thả
 * đổi thứ tự cột, phân trang.
 *
 * Chỉ lo phần TRÌNH BÀY. Việc gọi API, lọc và giữ state trang vẫn nằm ở trang
 * gọi nó — nhờ vậy bảng dùng được cả với danh sách phân trang phía server
 * (nhân sự, công ty) lẫn danh sách nạp một lần (nhân sự thuộc phòng ban).
 */
export function DataTable<T>({
  columns,
  rows,
  getRowId,
  isLoading,
  isError,
  emptyMessage = 'Không có dữ liệu.',
  errorMessage = 'Không tải được danh sách. Kiểm tra kết nối hoặc quyền truy cập.',
  onRowClick,
  toolbar,
  storageKey,
  pagination,
  fillHeight = false,
}: DataTableProps<T>) {
  const {
    layout,
    orderedColumns,
    visibleColumns,
    toggleColumn,
    setColumnWidth,
    setColumnWidths,
    setColumnColor,
    moveColumn,
    togglePin,
    resetLayout,
  } = useTableLayout(columns, storageKey)

  const { drag, startDrag } = useColumnDrag(moveColumn)
  const tableRef = useRef<HTMLTableElement>(null)

  const columnCount = visibleColumns.length
  const widthOf = (column: DataTableColumn<T>) =>
    layout.columnWidths[column.key] ?? column.width

  /**
   * Cột ghim theo đúng thứ tự đang hiện (chúng luôn đứng đầu — xem
   * `useTableLayout`). Mốc `left` do `usePinnedOffsets` ĐO TỪ DOM.
   */
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

  /**
   * Co MỌI cột đang hiện cho vừa nội dung — như nháy đúp vào từng vạch kéo giãn
   * nhưng làm một lượt. Đo trên DOM thật nên số thứ tự cột lấy theo hàng đang
   * hiện (khác thứ tự khai báo khi có cột ẩn / cột ghim).
   *
   * Ghi cả bảng bằng MỘT lần lưu: gọi `setColumnWidth` từng cột thì mỗi lần lại
   * lưu đè lên `layout` cũ đọc được lúc dựng hàm, chỉ cột cuối sống sót.
   */
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

  /**
   * Class của ô thuộc cột ghim. Nền `bg-inherit` để ăn theo nền của HÀNG (hàng
   * phải có nền ĐỤC — xem `ROW_BG`), nếu để trong suốt thì phần bảng cuộn qua
   * bên dưới sẽ lộ xuyên qua cột đang dính.
   */
  const pinClass = (key: string) =>
    pinnedKeys.includes(key) &&
    cn(
      // MỌI ô ghim đều tắt `border-r` và tự vẽ vạch bằng `inset shadow`: ô dính
      // nằm đè lên ô kế bên, để cả hai cùng có đường kẻ thì thành vạch đôi.
      'sticky z-20 border-r-0 bg-inherit',
      // Vạch luôn MẢNH 1px như mọi cột khác — vạch dày ở cột ghim cuối trông
      // như bị kẻ viền chồng lên nhau. Ranh giới phần đứng yên / phần đang trôi
      // báo bằng bóng đổ, và chỉ khi bảng đã cuộn ngang.
      'shadow-[inset_-1px_0_0_0_var(--border)]',
      key === lastPinnedKey &&
        scrolledX &&
        'shadow-[inset_-1px_0_0_0_var(--border),6px_0_8px_-6px_rgb(0_0_0/0.18)]',
    )

  /** `left` của ô dính; `undefined` nếu cột không ghim (hoặc chưa đo xong). */
  const pinOffset = (key: string) => pinnedOffsets[key]

  return (
    <div className={cn('flex flex-col', fillHeight && 'min-h-0 flex-1')}>
      {(toolbar || columns.some((c) => c.hideable !== false)) && (
        <div className="mb-4 flex shrink-0 flex-wrap items-center gap-3">
          {toolbar}
          <div className="ml-auto">
            <ColumnVisibilityMenu
              // Menu liệt kê theo thứ tự đang xem, không theo thứ tự khai báo —
              // kéo cột xong mà menu vẫn xếp kiểu cũ thì rất khó dò.
              columns={orderedColumns}
              hiddenColumns={layout.hiddenColumns}
              pinnedColumns={layout.pinnedColumns}
              columnColors={layout.columnColors}
              onToggle={toggleColumn}
              onTogglePin={togglePin}
              onAutoFitAll={autoFitAll}
              onColorChange={setColumnColor}
              onReset={resetLayout}
            />
          </div>
        </div>
      )}

      {/*
        Khung viền bao cả bảng; `overflow-hidden` để 4 góc bo không bị ô đè lên.

        `isolate` (isolation: isolate) TẠO NGỮ CẢNH XẾP LỚP riêng: mọi `z-index`
        của hàng tiêu đề dính và cột ghim bên trong chỉ so với nhau, không thể
        trồi lên trên thanh tiêu đề của trang (z-10) khi cuộn.
      */}
      <div
        className={cn(
          'isolate overflow-hidden rounded-lg border',
          fillHeight && 'flex min-h-0 flex-1 flex-col',
        )}
      >
        {/*
          `table-fixed`: độ rộng cột do khai báo/kéo giãn quyết định, không bị nội
          dung dài trong một ô kéo cả cột phình ra. Không có nó thì kéo giãn xong
          trình duyệt lại tự tính lại và cột nhảy về chỗ cũ.
        */}
        <Table
          ref={tableRef}
          className="table-fixed"
          containerClassName={cn(fillHeight && 'min-h-0 flex-1 overflow-auto')}
        >
          {/*
            Nền hàng tiêu đề phải ĐỤC (`bg-muted`, không phải `/60`): vừa để
            dòng trôi qua bên dưới không lộ ra khi tiêu đề dính đỉnh, vừa để ô
            của cột ghim `bg-inherit` che được phần bảng cuộn ngang phía sau.
          */}
          <TableHeader className={cn('bg-muted', fillHeight && 'sticky top-0 z-30')}>
            {/*
              `hover:bg-muted` KHÔNG thừa: `TableRow` của shadcn mặc định có
              `hover:bg-muted/50` — nền CÓ ALPHA. Rê chuột lên hàng tiêu đề đang
              dính đỉnh là nó trong suốt một nửa, các dòng trôi bên dưới hiện
              xuyên qua (và ô cột ghim `bg-inherit` cũng lộ theo). Ghi đè bằng
              đúng màu đục để hover không đổi gì cả.
            */}
            <TableRow ref={headerRowRef} className="bg-muted hover:bg-muted">
              {visibleColumns.map((column) => (
                <ColumnHeaderCell
                  key={column.key}
                  column={column}
                  width={widthOf(column)}
                  className={cn(HEAD_CELL, alignClass(column.align), pinClass(column.key))}
                  colorStyle={columnColorStyle(layout.columnColors[column.key], 'head')}
                  pinnedOffset={pinOffset(column.key)}
                  minWidth={column.minWidth ?? DEFAULT_MIN_WIDTH}
                  dragging={drag?.fromKey === column.key}
                  dropSide={drag?.overKey === column.key ? drag.side : null}
                  onResize={(next) => setColumnWidth(column.key, next)}
                  onDragStart={(event) => startDrag(event, column.key, column.header)}
                />
              ))}
            </TableRow>
          </TableHeader>

          {/*
            `TableBody` của shadcn bỏ `border-b` ở dòng cuối — hợp lý khi bảng
            kết thúc sát viền khung (hai đường sẽ chồng nhau). Nhưng ở chế độ
            fit chiều cao còn khoảng trống bên dưới, thiếu vạch đó là bảng hở đáy.
          */}
          <TableBody className={cn(fillHeight && '[&_tr:last-child]:border-b')}>
            {isLoading &&
              Array.from({ length: 5 }).map((_, index) => (
                <TableRow key={`skeleton-${index}`}>
                  <TableCell colSpan={columnCount} className={BODY_CELL}>
                    <Skeleton className="h-5 w-full" />
                  </TableCell>
                </TableRow>
              ))}

            {!isLoading && isError && (
              <TableRow>
                <TableCell
                  colSpan={columnCount}
                  className={cn(SPAN_CELL, 'text-destructive')}
                >
                  {errorMessage}
                </TableCell>
              </TableRow>
            )}

            {!isLoading && !isError && rows?.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={columnCount}
                  className={cn(SPAN_CELL, 'text-muted-foreground')}
                >
                  {emptyMessage}
                </TableCell>
              </TableRow>
            )}

            {!isLoading &&
              !isError &&
              rows?.map((row) => (
                <TableRow
                  key={getRowId(row)}
                  className={cn(ROW_BG, onRowClick && 'cursor-pointer')}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                >
                  {visibleColumns.map((column) => {
                    const content = column.cell(row)
                    return (
                      <TableCell
                        key={column.key}
                        style={{
                          width: widthOf(column),
                          left: pinOffset(column.key),
                          // Màu cột đặt SAU nền của hàng: ô đã tô màu giữ nguyên
                          // màu đó kể cả khi rê chuột, đúng ý "đánh dấu cột".
                          ...columnColorStyle(layout.columnColors[column.key], 'cell'),
                        }}
                        className={cn(
                          BODY_CELL,
                          alignClass(column.align),
                          pinClass(column.key),
                        )}
                      >
                        {/*
                          Bọc `truncate` giống ô tiêu đề: kéo cột hẹp lại thì chữ
                          cắt bằng dấu "…" thay vì bị xén cụt giữa chừng. Đặt trên
                          bọc chứ không trên `<td>` vì `text-overflow` chỉ ăn ở
                          khối chứa trực tiếp dòng chữ.
                        */}
                        <div
                          className="truncate"
                          title={typeof content === 'string' ? content : undefined}
                        >
                          {content}
                        </div>
                      </TableCell>
                    )
                  })}
                </TableRow>
              ))}
          </TableBody>
        </Table>
      </div>

      {pagination && <DataTablePagination {...pagination} />}

      {/* Nhãn bám theo con trỏ trong lúc kéo cột — tự vẽ nên bám sát từng khung
          hình, khác ảnh kéo mờ và trễ nhịp của HTML5 drag-and-drop. */}
      {drag && (
        <div
          className="pointer-events-none fixed z-50 -translate-y-1/2 translate-x-3 rounded-md border bg-popover px-2 py-1 text-xs font-medium text-popover-foreground shadow-md"
          style={{ left: drag.x, top: drag.y }}
        >
          {drag.label}
        </div>
      )}
    </div>
  )
}

function alignClass(align: DataTableColumn<unknown>['align']) {
  if (align === 'right') return 'text-right'
  if (align === 'center') return 'text-center'
  return undefined
}
