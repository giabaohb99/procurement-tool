import { Columns3, Eye, EyeOff, Pin, PinOff, RotateCcw } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/utils/cn'
import type { DataTableColumn } from './types'

interface ColumnVisibilityMenuProps<T> {
  columns: DataTableColumn<T>[]
  hiddenColumns: string[]
  pinnedColumns: string[]
  onToggle: (key: string) => void
  onTogglePin: (key: string) => void
  onReset: () => void
}

/**
 * Menu tùy biến cột: bật/tắt hiển thị và GHIM cột sang trái (dính lại khi cuộn
 * ngang), kèm nút trả bảng về mặc định.
 *
 * Không dùng `DropdownMenuCheckboxItem` như trước: mỗi dòng giờ có hai nút bấm
 * độc lập (ẩn/hiện và ghim), nhét vào một mục "chọn được" thì bấm chỗ nào cũng
 * thành tick ẩn/hiện.
 */
export function ColumnVisibilityMenu<T>({
  columns,
  hiddenColumns,
  pinnedColumns,
  onToggle,
  onTogglePin,
  onReset,
}: ColumnVisibilityMenuProps<T>) {
  if (columns.length === 0) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        {/* Chỉ chữ "Cột": số cột đang ẩn/ghim đã thấy ngay trong menu, đưa lên
            nút chỉ làm nhãn dài ra mà không giúp quyết định gì. */}
        <Button variant="outline">
          <Columns3 />
          Cột
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-72">
        <DropdownMenuLabel className="flex items-center justify-between font-normal text-muted-foreground">
          <span>Cột hiển thị</span>
          <span>Ghim</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {/* Bảng nhiều cột (Tiến độ mua hàng ~24 cột) -> danh sách tự cuộn. */}
        <div className="max-h-80 overflow-y-auto">
          {columns.map((column) => {
            const hidden = hiddenColumns.includes(column.key)
            const pinned = pinnedColumns.includes(column.key)
            // Cột `hideable: false` luôn phải hiện -> khóa nút ẩn, vẫn cho ghim.
            const canHide = column.hideable !== false

            return (
              <div
                key={column.key}
                className="flex items-center gap-1 rounded-sm px-2 py-1 hover:bg-accent"
              >
                <button
                  type="button"
                  disabled={!canHide}
                  onClick={() => onToggle(column.key)}
                  title={canHide ? 'Ẩn / hiện cột' : 'Cột này luôn hiển thị'}
                  className={cn(
                    'flex min-w-0 flex-1 items-center gap-2 py-1 text-left text-sm',
                    'disabled:cursor-not-allowed disabled:opacity-60',
                    hidden && 'text-muted-foreground',
                  )}
                >
                  {hidden ? (
                    <EyeOff className="size-4 shrink-0 text-muted-foreground" />
                  ) : (
                    <Eye className="size-4 shrink-0 text-muted-foreground" />
                  )}
                  <span className="truncate">{column.header}</span>
                </button>

                <button
                  type="button"
                  onClick={() => onTogglePin(column.key)}
                  title={pinned ? 'Bỏ ghim cột' : 'Ghim cột sang trái'}
                  aria-pressed={pinned}
                  className={cn(
                    'grid size-7 shrink-0 place-items-center rounded-md text-muted-foreground',
                    'hover:bg-background hover:text-foreground',
                    pinned && 'bg-background text-primary',
                  )}
                >
                  {pinned ? <PinOff className="size-4" /> : <Pin className="size-4" />}
                </button>
              </div>
            )
          })}
        </div>

        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={onReset}>
          <RotateCcw />
          Khôi phục mặc định
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
