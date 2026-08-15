import type { Editor } from '@tiptap/react'
import { Table as TableIcon } from 'lucide-react'
import { useRef, useState, type KeyboardEvent } from 'react'

import { Button } from '@/shared/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

interface TableMenuProps {
  editor: Editor
}

const GRID_ROWS = 10
const GRID_COLUMNS = 10

interface GridSize {
  rows: number
  columns: number
}

/**
 * Nhóm lệnh về BẢNG.
 *
 * Nút mở thẳng lưới chọn kích thước như Word thay vì buộc mọi bảng là 3×3.
 * Các lệnh sửa cấu trúc bảng nằm trong menu chuột phải ngay tại ô đang soạn.
 */
export function TableMenu({ editor }: TableMenuProps) {
  const [open, setOpen] = useState(false)
  const [activeSize, setActiveSize] = useState<GridSize | null>(null)
  const cellRefs = useRef<Array<HTMLButtonElement | null>>([])

  function cellIndex(rows: number, columns: number) {
    return (rows - 1) * GRID_COLUMNS + columns - 1
  }

  function moveTo(rows: number, columns: number, focus = false) {
    const next = {
      rows: Math.min(GRID_ROWS, Math.max(1, rows)),
      columns: Math.min(GRID_COLUMNS, Math.max(1, columns)),
    }
    setActiveSize(next)
    if (focus) cellRefs.current[cellIndex(next.rows, next.columns)]?.focus()
  }

  function handleGridKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    const rows = Number(event.currentTarget.dataset.row)
    const columns = Number(event.currentTarget.dataset.column)
    const nextByKey: Partial<Record<string, GridSize>> = {
      ArrowLeft: { rows, columns: columns - 1 },
      ArrowRight: { rows, columns: columns + 1 },
      ArrowUp: { rows: rows - 1, columns },
      ArrowDown: { rows: rows + 1, columns },
      Home: { rows, columns: 1 },
      End: { rows, columns: GRID_COLUMNS },
    }
    const next = nextByKey[event.key]
    if (!next) return

    event.preventDefault()
    event.stopPropagation()
    moveTo(next.rows, next.columns, true)
  }

  function insertTable(rows: number, columns: number) {
    editor.chain().focus().insertTable({ rows, cols: columns, withHeaderRow: true }).run()
    setOpen(false)
  }

  return (
    <Popover
      open={open}
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen)
        if (nextOpen) setActiveSize(null)
      }}
    >
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          title="Chèn bảng"
          aria-label="Chèn bảng"
          aria-expanded={open}
          onMouseDown={(event) => event.preventDefault()}
        >
          <TableIcon className="size-4" />
        </Button>
      </PopoverTrigger>

      <PopoverContent
        align="start"
        className="w-[19rem] max-w-[calc(100vw-1rem)] p-3"
        onOpenAutoFocus={(event) => {
          event.preventDefault()
          cellRefs.current[0]?.focus()
        }}
        onCloseAutoFocus={(event) => event.preventDefault()}
      >
        <div className="mb-2 flex items-center justify-between gap-3">
          <p className="text-sm font-medium">Chèn bảng</p>
          <output aria-live="polite" className="text-xs text-muted-foreground tabular-nums">
            {activeSize ? `${activeSize.columns} cột × ${activeSize.rows} hàng` : 'Chọn kích thước'}
          </output>
        </div>

        <div
          role="grid"
          aria-label="Chọn số cột và hàng của bảng"
          aria-rowcount={GRID_ROWS}
          aria-colcount={GRID_COLUMNS}
          className="grid grid-cols-10 gap-1"
          onPointerLeave={() => setActiveSize(null)}
        >
          {Array.from({ length: GRID_ROWS }, (_, rowIndex) => {
            const rows = rowIndex + 1
            return (
              <div key={rows} role="row" className="contents">
                {Array.from({ length: GRID_COLUMNS }, (_, columnIndex) => {
                  const columns = columnIndex + 1
                  const active = Boolean(
                    activeSize && rows <= activeSize.rows && columns <= activeSize.columns,
                  )
                  const current = activeSize
                    ? rows === activeSize.rows && columns === activeSize.columns
                    : rows === 1 && columns === 1

                  return (
                    <button
                      key={columns}
                      ref={(element) => {
                        cellRefs.current[cellIndex(rows, columns)] = element
                      }}
                      type="button"
                      role="gridcell"
                      data-row={rows}
                      data-column={columns}
                      tabIndex={current ? 0 : -1}
                      aria-selected={active}
                      aria-label={`Chèn bảng ${columns} cột, ${rows} hàng`}
                      title={`${columns} cột × ${rows} hàng`}
                      className={cn(
                        'size-6 rounded-[3px] border transition-colors outline-none',
                        'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
                        active
                          ? 'border-primary bg-primary/15'
                          : 'border-border bg-background hover:border-primary/60',
                      )}
                      onFocus={(event) => {
                        if (event.currentTarget.matches(':focus-visible')) {
                          moveTo(rows, columns)
                        }
                      }}
                      onPointerEnter={() => moveTo(rows, columns)}
                      onKeyDown={handleGridKeyDown}
                      onClick={() => insertTable(rows, columns)}
                    />
                  )
                })}
              </div>
            )
          })}
        </div>
      </PopoverContent>
    </Popover>
  )
}
