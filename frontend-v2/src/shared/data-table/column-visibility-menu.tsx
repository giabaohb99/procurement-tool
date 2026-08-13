import { Ban, Check, Columns3, Eye, EyeOff, Palette, Pin, PinOff, RotateCcw, Scaling } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/utils/cn'
import { COLUMN_COLORS, findColumnColor, isCustomColor } from './column-color-palette'
import type { DataTableColumn } from './types'

interface ColumnVisibilityMenuProps<T> {
  columns: DataTableColumn<T>[]
  hiddenColumns: string[]
  pinnedColumns: string[]
  columnColors: Record<string, string>
  onToggle: (key: string) => void
  onTogglePin: (key: string) => void
  /** Co giãn MỌI cột đang hiện cho vừa nội dung. */
  onAutoFitAll: () => void
  onColorChange: (key: string, colorId: string) => void
  onReset: () => void
}

const ICON_BUTTON =
  'grid size-7 shrink-0 place-items-center rounded-md text-muted-foreground hover:bg-background hover:text-foreground disabled:pointer-events-none disabled:opacity-40'

/**
 * Menu tùy biến cột: bật/tắt hiển thị, GHIM sang trái (dính khi cuộn ngang),
 * co giãn vừa nội dung và tô màu từng cột, kèm nút trả bảng về mặc định.
 *
 * Không dùng `DropdownMenuCheckboxItem`: mỗi dòng có nhiều nút bấm độc lập,
 * nhét vào một mục "chọn được" thì bấm chỗ nào cũng thành tick ẩn/hiện.
 */
export function ColumnVisibilityMenu<T>({
  columns,
  hiddenColumns,
  pinnedColumns,
  columnColors,
  onToggle,
  onTogglePin,
  onAutoFitAll,
  onColorChange,
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

      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuLabel className="flex items-center justify-between font-normal text-muted-foreground">
          <span>Cột hiển thị</span>
          <span>Màu · Ghim</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {/* Bảng nhiều cột (Tiến độ mua hàng ~24 cột) -> danh sách tự cuộn. */}
        <div className="max-h-80 overflow-y-auto">
          {columns.map((column) => {
            const hidden = hiddenColumns.includes(column.key)
            const pinned = pinnedColumns.includes(column.key)
            // Cột `hideable: false` luôn phải hiện -> khóa nút ẩn, vẫn cho ghim.
            const canHide = column.hideable !== false
            const color = findColumnColor(columnColors[column.key])

            return (
              <div
                key={column.key}
                className="flex items-center gap-0.5 rounded-sm px-2 py-1 hover:bg-accent"
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

                <DropdownMenuSub>
                  <DropdownMenuSubTrigger
                    title="Tô màu cột"
                    // Bỏ hết dáng "mục menu" mặc định để nút này nhìn như hai
                    // nút biểu tượng bên cạnh; mũi tên phụ của SubTrigger ẩn đi.
                    className={cn(ICON_BUTTON, 'px-0 py-0 [&>svg:last-child]:hidden')}
                  >
                    {color ? (
                      <span
                        className="size-4 rounded-full border"
                        style={{ backgroundColor: color.value }}
                      />
                    ) : (
                      <Palette className="size-4" />
                    )}
                  </DropdownMenuSubTrigger>
                  <DropdownMenuSubContent className="w-44">
                    <DropdownMenuItem onSelect={() => onColorChange(column.key, '')}>
                      <Ban className="text-muted-foreground" />
                      Không màu
                      {!color && <Check className="ml-auto size-4" />}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    {COLUMN_COLORS.map((option) => (
                      <DropdownMenuItem
                        key={option.id}
                        onSelect={() => onColorChange(column.key, option.id)}
                      >
                        <span
                          className="size-4 rounded-full border"
                          style={{ backgroundColor: option.value }}
                        />
                        {option.label}
                        {color?.id === option.id && <Check className="ml-auto size-4" />}
                      </DropdownMenuItem>
                    ))}
                    <DropdownMenuSeparator />
                    {/* `preventDefault`: chọn màu xong menu phải Ở LẠI, đóng cái
                        là bảng chọn màu của hệ điều hành cũng tắt theo. */}
                    <DropdownMenuItem
                      onSelect={(event) => event.preventDefault()}
                      className="cursor-pointer"
                      asChild
                    >
                      <label>
                        <span
                          className="size-4 rounded-full border"
                          style={{
                            background: isCustomColor(color?.id)
                              ? color?.value
                              : 'conic-gradient(#dc2626,#d97706,#16a34a,#0891b2,#2563eb,#7c3aed,#db2777,#dc2626)',
                          }}
                        />
                        Màu tùy chỉnh…
                        {isCustomColor(color?.id) && <Check className="ml-auto size-4" />}
                        <input
                          type="color"
                          className="sr-only"
                          value={isCustomColor(color?.id) ? color!.value : '#2563eb'}
                          onChange={(event) => onColorChange(column.key, event.target.value)}
                        />
                      </label>
                    </DropdownMenuItem>
                  </DropdownMenuSubContent>
                </DropdownMenuSub>

                <button
                  type="button"
                  onClick={() => onTogglePin(column.key)}
                  title={pinned ? 'Bỏ ghim cột' : 'Ghim cột sang trái'}
                  aria-pressed={pinned}
                  className={cn(ICON_BUTTON, pinned && 'bg-background text-primary')}
                >
                  {pinned ? <PinOff className="size-4" /> : <Pin className="size-4" />}
                </button>
              </div>
            )
          })}
        </div>

        <DropdownMenuSeparator />
        {/* Một nút cho CẢ BẢNG: chỉnh từng cột một thì đã có cách nhanh hơn —
            nháy đúp vào vạch kéo giãn ngay trên tiêu đề cột đó. */}
        <DropdownMenuItem onSelect={onAutoFitAll}>
          <Scaling />
          Vừa nội dung tất cả cột
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={onReset}>
          <RotateCcw />
          Khôi phục mặc định
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
