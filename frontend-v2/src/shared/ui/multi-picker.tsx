import { Check, Search, X } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

/**
 * Định danh của một mục.
 *
 * Cho phép cả CHUỖI vì có chỗ mục không phải một bản ghi đơn mà là một CẶP —
 * ví dụ (phòng ban × pháp nhân) ở khối phạm vi áp dụng của văn bản, khóa dạng
 * `"4:1"`. Ép về số thì hai phòng cùng tên ở hai công ty dính làm một.
 */
export type MultiPickerId = number | string

export interface MultiPickerOption {
  id: MultiPickerId
  label: string
  /** Chữ mờ bên phải: mã, số hiệu, chức danh… — thứ để phân biệt hai dòng trùng tên. */
  hint?: string
}

/**
 * `Id` bám theo kiểu của `value`, nên nơi gọi truyền `number[]` vẫn nhận lại
 * `number[]` ở `onChange` — không phải ép kiểu ở mọi chỗ đang dùng.
 */
interface MultiPickerProps<Id extends MultiPickerId = MultiPickerId> {
  value: Id[]
  onChange: (ids: Id[]) => void
  options: (Omit<MultiPickerOption, 'id'> & { id: Id })[]
  placeholder: string
  searchPlaceholder?: string
  emptyMessage?: string
  disabled?: boolean
}

/** Số dòng tối đa trong danh sách thả xuống — dài hơn thì bắt gõ tìm. */
const MAX_VISIBLE = 50

/**
 * Chọn NHIỀU mục từ một danh sách có sẵn: nút mở, ô tìm, danh sách tick, và dải
 * chip của những mục đã chọn.
 *
 * Dùng cho nhân sự, loại văn bản, văn bản… — bất cứ thứ gì rút gọn được về
 * `{id, label, hint}`. Trước đây chỉ có bản riêng cho nhân sự, và mỗi lần cần
 * chọn nhiều thứ khác lại chép ra một bản gần giống.
 */
export function MultiPicker<Id extends MultiPickerId = MultiPickerId>({
  value,
  onChange,
  options,
  placeholder,
  searchPlaceholder = 'Tìm…',
  emptyMessage = 'Không tìm thấy mục nào.',
  disabled,
}: MultiPickerProps<Id>) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')

  const selected = useMemo(
    () => value.map((id) => options.find((item) => item.id === id)).filter(Boolean) as typeof options,
    [value, options],
  )

  // Giữ CẢ danh sách lọc được, không chỉ phần bày ra: nút "Chọn tất cả" phải áp
  // cho mọi mục khớp từ khóa, kể cả những mục bị `MAX_VISIBLE` cắt bớt — người
  // dùng gõ tìm rồi bấm chọn tất cả là muốn hết chỗ đó, không phải 50 dòng đầu.
  const filtered = useMemo(() => {
    const needle = keyword.trim().toLowerCase()
    if (!needle) return options
    return options.filter((item) =>
      [item.label, item.hint].some((field) => (field ?? '').toLowerCase().includes(needle)),
    )
  }, [options, keyword])

  const matches = useMemo(() => filtered.slice(0, MAX_VISIBLE), [filtered])

  /** Đã tick hết phần đang lọc chưa — quyết định nút là "Chọn" hay "Bỏ chọn". */
  const allPicked = filtered.length > 0 && filtered.every((item) => value.includes(item.id))

  function toggle(id: Id) {
    onChange(value.includes(id) ? value.filter((item) => item !== id) : [...value, id])
  }

  /** Tick / bỏ tick TOÀN BỘ phần đang lọc, giữ nguyên các mục đã chọn ngoài đó. */
  function toggleAll() {
    const ids = filtered.map((item) => item.id)
    if (allPicked) {
      const dropped = new Set(ids)
      onChange(value.filter((id) => !dropped.has(id)))
      return
    }
    onChange([...value, ...ids.filter((id) => !value.includes(id))])
  }

  return (
    <div className="space-y-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            disabled={disabled}
            className="w-full justify-start font-normal text-muted-foreground"
          >
            <Search className="size-4" />
            {placeholder}
          </Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-80 p-0">
          <div className="border-b p-2">
            <Input
              autoFocus
              placeholder={searchPlaceholder}
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
            />
          </div>
          {filtered.length > 0 && (
            <div className="flex items-center justify-between gap-2 border-b px-2 py-1.5">
              <button
                type="button"
                onClick={toggleAll}
                className="rounded-sm px-1 py-0.5 text-sm font-medium text-primary hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              >
                {allPicked ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
                <span className="ml-1 font-normal text-muted-foreground tabular-nums">
                  ({filtered.length})
                </span>
              </button>
              {/* Nhắc rõ nút đang áp cho phần lọc được, không phải cả danh sách. */}
              {keyword.trim() && (
                <span className="text-xs text-muted-foreground">theo từ khóa đang tìm</span>
              )}
            </div>
          )}

          <div className="max-h-72 overflow-y-auto p-1">
            {matches.length === 0 && (
              <p className="px-2 py-4 text-center text-sm text-muted-foreground">
                {emptyMessage}
              </p>
            )}
            {matches.map((item) => {
              const checked = value.includes(item.id)
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => toggle(item.id)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent',
                    checked && 'bg-accent/50',
                  )}
                >
                  <Check className={cn('size-4 shrink-0', !checked && 'invisible')} />
                  <span className="flex-1 truncate">{item.label}</span>
                  {item.hint && (
                    <span className="shrink-0 text-xs text-muted-foreground">{item.hint}</span>
                  )}
                </button>
              )
            })}

            {/* Danh sách bị cắt bớt thì phải nói ra, không thì nhìn như đã hết
                mục — trong khi "Chọn tất cả" vẫn tính cả phần chưa bày. */}
            {filtered.length > matches.length && (
              <p className="px-2 py-2 text-center text-xs text-muted-foreground">
                Còn {filtered.length - matches.length} mục nữa — gõ để thu hẹp danh sách.
              </p>
            )}
          </div>
        </PopoverContent>
      </Popover>

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {selected.map((item) => (
            <Badge key={item.id} variant="secondary" className="gap-1 font-normal">
              {item.label}
              <button
                type="button"
                aria-label={`Bỏ ${item.label}`}
                onClick={() => toggle(item.id)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="size-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}
