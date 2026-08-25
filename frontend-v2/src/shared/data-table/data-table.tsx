import { useQueryClient } from '@tanstack/react-query'
import { RotateCw } from 'lucide-react'
import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'
import { Table, TableBody, TableCell, TableHeader, TableRow } from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { columnColorStyle } from './column-color-palette'
import { ColumnHeaderCell } from './column-header-cell'
import { ColumnVisibilityMenu } from './column-visibility-menu'
import { DataTablePagination } from './data-table-pagination'
import { measureColumnContentWidth } from './measure-column-width'
import { columnLabel } from './required-header'
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
  'relative h-10 px-3 text-[13px] font-bold text-slate-900 dark:text-slate-100 bg-slate-200/80 dark:bg-slate-800/90 shadow-[inset_-1px_0_0_0_var(--border),inset_0_-1px_0_0_var(--border)] last:shadow-[inset_0_-1px_0_0_var(--border)]'
const BODY_CELL = 'min-h-9 border-r px-3 py-1.5 last:border-r-0 align-middle text-[13.5px] text-foreground'
/**
 * Thân bảng HÀNG CHẴN LẺ ĐẬM NHẠT XEN KẼ (Zebra striping đậm rõ màu):
 * Hàng lẻ (odd): nền trắng bg-card
 * Hàng chẵn (even): nền xám rõ màu `even:bg-slate-100`
 * Hover: `hover:bg-sky-100`
 *
 * ⚠️ **NỀN HÀNG PHẢI ĐỤC, TUYỆT ĐỐI KHÔNG ALPHA.** Ô của cột GHIM lấy
 * `bg-inherit` từ hàng (xem `PIN_*` bên dưới), nên hàng trong suốt bao nhiêu thì
 * ô ghim trong suốt bấy nhiêu — và nội dung đang trôi ngang BÊN DƯỚI nó hiện
 * xuyên qua. Lỗi thật đã bắt được 24/08/2026: nền hover là `bg-sky-100/70` nên
 * cứ rê chuột vào một hàng của bảng đang cuộn ngang là chữ ở cột ghim chồng lên
 * chữ của cột đang trôi qua, đọc không ra chữ nào.
 *
 * Cùng một bài học đã ghi ở hàng TIÊU ĐỀ bên dưới (`bg-muted hover:bg-muted`)
 * mà lúc đó chưa soi lại thân bảng.
 *
 * Mấy lớp `dark:` giữ nguyên vì chưa có đường nào bật chế độ tối; ngày bật lên
 * thì phải soi lại đúng chỗ này — `dark:even:bg-slate-800/60` cũng đang có alpha.
 */
const ROW_BG = 'group odd:bg-card even:bg-slate-100 dark:even:bg-slate-800/60 hover:bg-sky-100 dark:hover:bg-slate-800 data-[state=selected]:bg-blue-100 dark:data-[state=selected]:bg-slate-700 transition-colors'
/** Ô báo trạng thái (đang tải / lỗi / rỗng) trải hết bảng — không kẻ dọc, cao hơn. */
const SPAN_CELL = 'h-20 px-3 text-center'

/**
 * Vạch kẻ của Ô CỘT GHIM, viết sẵn thành hằng chứ không ghép chuỗi lúc chạy:
 * Tailwind quét MÃ NGUỒN để sinh class, tên class ghép động sẽ không có CSS nào
 * cả. Hậu tố `_HEAD` kèm vạch đáy của hàng tiêu đề, `_DROP` kèm bóng đổ báo có
 * nội dung đang trôi bên dưới.
 *
 * Bản `last:` của cột ghim phải là BẮT BUỘC với cột dính bên phải: nó luôn là ô
 * cuối hàng, mà `HEAD_CELL` có sẵn `last:shadow-…` (chỉ vạch đáy) — biến thể
 * `last:` có độ ưu tiên cao hơn class thường nên không ghi đè đúng biến thể đó
 * thì vạch trái bị nuốt mất. Đó chính là lỗi "ghim cột phải mà không có border".
 */
const PIN_LEFT = 'shadow-[inset_-1px_0_0_0_var(--border)]'
const PIN_LEFT_HEAD = 'shadow-[inset_-1px_0_0_0_var(--border),inset_0_-1px_0_0_var(--border)]'
const PIN_LEFT_DROP = 'shadow-[inset_-1px_0_0_0_var(--border),6px_0_8px_-6px_rgb(0_0_0/0.18)]'
const PIN_LEFT_HEAD_DROP =
  'shadow-[inset_-1px_0_0_0_var(--border),inset_0_-1px_0_0_var(--border),6px_0_8px_-6px_rgb(0_0_0/0.18)]'
const PIN_RIGHT = 'shadow-[inset_1px_0_0_0_var(--border)] last:shadow-[inset_1px_0_0_0_var(--border)]'
const PIN_RIGHT_HEAD =
  'shadow-[inset_1px_0_0_0_var(--border),inset_0_-1px_0_0_var(--border)] last:shadow-[inset_1px_0_0_0_var(--border),inset_0_-1px_0_0_var(--border)]'

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  rows: T[] | undefined
  getRowId: (row: T) => string | number

  isLoading?: boolean
  isError?: boolean
  emptyMessage?: string
  errorMessage?: string

  onRowClick?: (row: T) => void
  /**
   * Việc chạy khi bấm nút Tải lại. Bỏ trống thì bảng tự làm mới MỌI query đang
   * hoạt động của trang — đúng ý "xem số mới nhất" ở gần hết màn danh sách, nên
   * không bắt từng trang phải khai lại.
   */
  onRefresh?: () => void | Promise<unknown>
  /** Nội dung chèn bên TRÁI menu "Cột" (ô tìm kiếm, select, nút Bộ lọc…). */
  toolbar?: ReactNode
  /** Có thì bảng nhớ cột ẩn + độ rộng + thứ tự cột vào localStorage theo khóa này. */
  storageKey?: string
  pagination?: PaginationConfig
  sortBy?: string
  sortDir?: 'asc' | 'desc'
  onSortChange?: (sortBy: string, sortDir: 'asc' | 'desc') => void
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
  onRefresh,
  toolbar,
  storageKey,
  pagination,
  sortBy,
  sortDir,
  onSortChange,
  fillHeight = false,
}: DataTableProps<T>) {
  const queryClient = useQueryClient()
  const [refreshing, setRefreshing] = useState(false)

  /**
   * Tải lại dữ liệu. Cờ `refreshing` do CHÍNH nút giữ (không dùng `isFetching`
   * của trang): vòng xoay phải chạy đủ trọn một nhịp bấm kể cả khi dữ liệu về
   * gần như tức thì, nếu không thì bấm xong chẳng thấy gì phản hồi.
   */
  const handleRefresh = useCallback(async () => {
    setRefreshing(true)
    try {
      await (onRefresh ? onRefresh() : queryClient.invalidateQueries({ type: 'active' }))
    } finally {
      setRefreshing(false)
    }
  }, [onRefresh, queryClient])
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
  const widthOf = (column: DataTableColumn<T>) => layout.columnWidths[column.key] ?? column.width

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

  const pinnedRightKeys = useMemo(
    () => visibleColumns.filter((column) => column.stickyRight).map((column) => column.key),
    [visibleColumns],
  )

  const { headerRowRef, pinnedOffsets, pinnedRightOffsets, scrolledX } = usePinnedOffsets(
    pinnedKeys,
    pinnedRightKeys,
  )
  const lastPinnedKey = pinnedKeys.at(-1)
  const beforePinnedRightKey = useMemo(() => {
    const firstRightIndex = visibleColumns.findIndex((column) => column.stickyRight)
    return firstRightIndex > 0 ? visibleColumns[firstRightIndex - 1]?.key : undefined
  }, [visibleColumns])

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
   *
   * `head` = ô này nằm ở hàng tiêu đề, phải kẻ thêm VẠCH ĐÁY: chuỗi shadow ở
   * đây ghi đè shadow của `HEAD_CELL` (tailwind-merge, cùng nhóm `shadow`, cái
   * sau thắng) nên không tự vẽ lại thì hàng tiêu đề thủng một đoạn ngay dưới
   * cột ghim.
   */
  const pinClass = (key: string, head = false) => {
    if (pinnedKeys.includes(key)) {
      const doBong = key === lastPinnedKey && scrolledX
      return cn(
        // MỌI ô ghim đều tắt `border-r` và tự vẽ vạch bằng `inset shadow`: ô dính
        // nằm đè lên ô kế bên, để cả hai cùng có đường kẻ thì thành vạch đôi.
        'sticky z-20 border-r-0 bg-inherit',
        // Vạch luôn MẢNH 1px như mọi cột khác — vạch dày ở cột ghim cuối trông
        // như bị kẻ viền chồng lên nhau. Ranh giới phần đứng yên / phần đang trôi
        // báo bằng bóng đổ, và chỉ khi bảng đã cuộn ngang.
        doBong
          ? head
            ? PIN_LEFT_HEAD_DROP
            : PIN_LEFT_DROP
          : head
            ? PIN_LEFT_HEAD
            : PIN_LEFT,
      )
    }

    if (pinnedRightKeys.includes(key)) {
      //  ⚠️ KHÔNG dùng `border-l`: preflight đặt `border-collapse: collapse`, ở
      //  chế độ đó viền thuộc về bảng chứ không thuộc ô, nên ô `position: sticky`
      //  bị bỏ mất viền — cột ghim phải trôi lơ lửng không một nét kẻ nào (đúng
      //  lỗi phải vá ở đây). Vạch vẽ bằng `inset shadow` như hàng tiêu đề dính.
      //
      //  Vạch của cột KẾ BÊN đã được tắt (`beforePinnedRightKey`) nên không có
      //  chuyện hai nét 1px nằm sát nhau.
      return cn('sticky z-20 border-r-0 border-l-0 bg-inherit', head ? PIN_RIGHT_HEAD : PIN_RIGHT)
    }

    return undefined
  }

  /** `left` của ô dính; `undefined` nếu cột không ghim (hoặc chưa đo xong). */
  const pinOffset = (key: string) => pinnedOffsets[key]
  /** `right` của ô thao tác cố định bên phải. */
  const pinRightOffset = (key: string) => pinnedRightOffsets[key]

  return (
    <div className={cn('flex flex-col', fillHeight && 'min-h-0 flex-1')}>
      {(toolbar || columns.some((c) => c.hideable !== false)) && (
        <div className="mb-4 flex shrink-0 flex-wrap items-center gap-3">
          {toolbar}
          <div className="ml-auto flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              title="Tải lại dữ liệu"
              aria-label="Tải lại dữ liệu"
              disabled={refreshing}
              onClick={handleRefresh}
            >
              <RotateCw className={cn('size-4', refreshing && 'animate-spin')} />
            </Button>

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
              onMove={moveColumn}
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
          {/*
            `[&_tr]:border-b-0` GỠ vạch đáy mà `TableHeader` của shadcn tự đặt
            lên hàng tiêu đề. Không thừa: ô tiêu đề đã tự vẽ vạch đáy bằng
            `inset shadow` (xem `HEAD_CELL`), giữ cả hai là hai đường 1px nằm sát
            nhau — hàng tiêu đề trông dày gấp đôi mọi đường kẻ khác trong bảng.
            Bỏ cái `border` chứ không bỏ cái `shadow`, vì `border-collapse` làm
            border của hàng tiêu đề dính đỉnh biến mất khi cuộn.
          */}
          <TableHeader
            className={cn('bg-muted [&_tr]:border-b-0', fillHeight && 'sticky top-0 z-30')}
          >
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
                  className={cn(HEAD_CELL, alignClass(column.align), pinClass(column.key, true))}
                  colorStyle={columnColorStyle(layout.columnColors[column.key], 'head')}
                  pinnedOffset={pinOffset(column.key)}
                  pinnedRightOffset={pinRightOffset(column.key)}
                  suppressRightDivider={column.key === beforePinnedRightKey}
                  minWidth={column.minWidth ?? DEFAULT_MIN_WIDTH}
                  draggable={!column.stickyRight}
                  dragging={drag?.fromKey === column.key}
                  dropSide={drag?.overKey === column.key ? drag.side : null}
                  sortDir={sortBy === column.key ? sortDir : null}
                  onSort={
                    onSortChange
                      ? () => {
                          const nextDir = sortBy === column.key && sortDir === 'asc' ? 'desc' : 'asc'
                          onSortChange(column.key, nextDir)
                        }
                      : undefined
                  }
                  onResize={(next) => setColumnWidth(column.key, next)}
                  onDragStart={(event) => startDrag(event, column.key, columnLabel(column.header))}
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
                <TableCell colSpan={columnCount} className={cn(SPAN_CELL, 'text-destructive')}>
                  {errorMessage}
                </TableCell>
              </TableRow>
            )}

            {!isLoading && !isError && rows?.length === 0 && (
              <TableRow>
                <TableCell colSpan={columnCount} className={cn(SPAN_CELL, 'text-muted-foreground')}>
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
                    let content = column.cell(row)
                    if (typeof content === 'string' && (content === '—' || content === '-')) {
                      content = ''
                    }
                    return (
                      <TableCell
                        key={column.key}
                        style={{
                          width: widthOf(column),
                          left: pinOffset(column.key),
                          right: pinRightOffset(column.key),
                          borderRightWidth: column.key === beforePinnedRightKey ? 0 : undefined,
                          // Màu cột đặt SAU nền của hàng: ô đã tô màu giữ nguyên
                          // màu đó kể cả khi rê chuột, đúng ý "đánh dấu cột".
                          ...columnColorStyle(layout.columnColors[column.key], 'cell'),
                        }}
                        className={cn(BODY_CELL, alignClass(column.align), pinClass(column.key))}
                      >
                        {/*
                          Bọc `truncate` giống ô tiêu đề: kéo cột hẹp lại thì chữ
                          cắt bằng dấu "…" thay vì bị xén cụt giữa chừng. Đặt trên
                          bọc chứ không trên `<td>` vì `text-overflow` chỉ ăn ở
                          khối chứa trực tiếp dòng chữ.
                        */}
                        <div
                          className={cn(
                            column.wrap ? 'leading-snug break-words whitespace-normal' : 'truncate',
                          )}
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
          className="pointer-events-none fixed z-50 translate-x-3 -translate-y-1/2 rounded-md border bg-popover px-2 py-1 text-xs font-medium text-popover-foreground shadow-md"
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
