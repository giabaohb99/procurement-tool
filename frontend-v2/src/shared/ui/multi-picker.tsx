import { Check, Search, X } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

export interface MultiPickerOption {
  id: number
  label: string
  /** Chữ mờ bên phải: mã, số hiệu, chức danh… — thứ để phân biệt hai dòng trùng tên. */
  hint?: string
}

interface MultiPickerProps {
  value: number[]
  onChange: (ids: number[]) => void
  options: MultiPickerOption[]
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
export function MultiPicker({
  value,
  onChange,
  options,
  placeholder,
  searchPlaceholder = 'Tìm…',
  emptyMessage = 'Không tìm thấy mục nào.',
  disabled,
}: MultiPickerProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')

  const selected = useMemo(
    () => value.map((id) => options.find((item) => item.id === id)).filter(Boolean) as MultiPickerOption[],
    [value, options],
  )

  const matches = useMemo(() => {
    const needle = keyword.trim().toLowerCase()
    const rows = needle
      ? options.filter((item) =>
          [item.label, item.hint].some((field) => (field ?? '').toLowerCase().includes(needle)),
        )
      : options
    return rows.slice(0, MAX_VISIBLE)
  }, [options, keyword])

  function toggle(id: number) {
    onChange(value.includes(id) ? value.filter((item) => item !== id) : [...value, id])
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
