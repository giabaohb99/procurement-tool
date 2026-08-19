import { Check, ChevronsUpDown, X } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

export interface SearchSelectOption {
  value: string
  label: string
}

interface SearchSelectProps {
  value: string
  onChange: (value: string) => void
  options: SearchSelectOption[]
  placeholder?: string
  searchPlaceholder?: string
  emptyMessage?: string
  disabled?: boolean
  /** Hiện nút xóa lựa chọn khi đang có giá trị. */
  clearable?: boolean
  /**
   * Cho nhãn xuống dòng thay vì cắt cụt. Bật ở ô nằm trong bảng nhiều cột —
   * xem hợp đồng hiển thị CR-090 trong `CLAUDE.md`.
   */
  wrap?: boolean
  size?: 'sm' | 'default'
  className?: string
}

/** Số dòng tối đa trong danh sách thả xuống — dài hơn thì bắt gõ tìm. */
const MAX_VISIBLE = 60

/**
 * Chọn MỘT mục từ danh sách dài, có ô tìm.
 *
 * `Select` của shadcn không tìm được, mà danh mục NCC / nhóm hàng / ĐVT lên tới
 * hàng trăm dòng — cuộn tay là không dùng nổi. Dựng trên `Popover + Input` chứ
 * không kéo thêm `cmdk` về chỉ để có một ô tìm.
 *
 * Giá trị đang lưu mà KHÔNG có trong `options` vẫn được hiện nguyên văn: dữ liệu
 * cũ hay có mã đã bị gỡ khỏi danh mục, giấu đi là người dùng tưởng ô trống rồi
 * chọn đè mất.
 */
export function SearchSelect({
  value,
  onChange,
  options,
  placeholder = 'Chọn…',
  searchPlaceholder = 'Tìm…',
  emptyMessage = 'Không tìm thấy mục nào.',
  disabled,
  clearable,
  wrap,
  size = 'default',
  className,
}: SearchSelectProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')

  const selectedLabel = useMemo(
    () => options.find((option) => option.value === value)?.label ?? value,
    [options, value],
  )

  const matches = useMemo(() => {
    const needle = keyword.trim().toLowerCase()
    const rows = needle
      ? options.filter((option) =>
          [option.label, option.value].some((field) => field.toLowerCase().includes(needle)),
        )
      : options
    return rows.slice(0, MAX_VISIBLE)
  }, [options, keyword])

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (!next) setKeyword('')
      }}
    >
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            'w-full justify-between gap-1 px-2 font-normal',
            size === 'sm' && 'h-8 text-sm',
            wrap ? 'h-auto min-h-8 items-start py-1.5 text-left' : 'truncate',
            !value && 'text-muted-foreground',
            className,
          )}
        >
          <span className={cn('flex-1', wrap ? 'whitespace-pre-wrap break-words' : 'truncate')}>
            {value ? selectedLabel : placeholder}
          </span>
          {clearable && value ? (
            <span
              role="button"
              tabIndex={-1}
              aria-label="Xóa lựa chọn"
              className="shrink-0 text-muted-foreground hover:text-foreground"
              onClick={(event) => {
                event.preventDefault()
                event.stopPropagation()
                onChange('')
              }}
            >
              <X className="size-4" />
            </span>
          ) : (
            <ChevronsUpDown className="size-4 shrink-0 opacity-50" />
          )}
        </Button>
      </PopoverTrigger>

      <PopoverContent align="start" className="w-(--radix-popover-trigger-width) min-w-64 p-0">
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
            <p className="px-2 py-4 text-center text-sm text-muted-foreground">{emptyMessage}</p>
          )}
          {matches.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => {
                onChange(option.value)
                setOpen(false)
              }}
              className={cn(
                'flex w-full items-start gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent',
                option.value === value && 'bg-accent/50',
              )}
            >
              <Check
                className={cn(
                  'mt-0.5 size-4 shrink-0',
                  option.value !== value && 'invisible',
                )}
              />
              <span className="flex-1 whitespace-pre-wrap break-words">{option.label}</span>
            </button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
