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
 * Chuẩn hóa để so: bỏ dấu, thường hóa.
 *
 * Người Việt gõ ô tìm thường KHÔNG bỏ dấu — "nghi phep", "phap nhan", "don vi".
 * So thô thì "nghi" không khớp "nghỉ" và người dùng kết luận là danh mục không
 * có mục đó, dù nó nằm ngay đấy (khách báo 25/08/2026 với loại văn bản «Giấy
 * nghỉ phép»).
 *
 * `normalize('NFD')` tách dấu thành ký tự tổ hợp riêng rồi xóa chúng đi. Riêng
 * **đ / Đ** không phải chữ d có dấu nên NFD không đụng tới, phải thay tay.
 *
 * Chỉ dùng để SO, không đụng tới chuỗi hiện ra — nhãn vẫn nguyên dấu.
 */
function stripDiacritics(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase()
}

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

  const { matches, remaining } = useMemo(() => {
    const needle = stripDiacritics(keyword.trim())
    const rows = needle
      ? options.filter((option) =>
          [option.label, option.value].some((field) => stripDiacritics(field).includes(needle)),
        )
      : options
    return { matches: rows.slice(0, MAX_VISIBLE), remaining: Math.max(rows.length - MAX_VISIBLE, 0) }
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
            //  `text-left` phải áp cho MỌI trường hợp: trình duyệt mặc định
            //  `button { text-align: center }`, mà chữ nằm trong `<span>` con
            //  nên `justify-between` của flex không cứu được — nó xếp vị trí
            //  cái span, còn chữ BÊN TRONG span vẫn căn giữa. Trước 25/08/2026
            //  `text-left` chỉ nằm ở nhánh `wrap`, nên ô chọn ở form dựng đứng
            //  hiện chữ giữa ô, lệch hẳn so với các ô nhập bên cạnh.
            //  `px-3` để thẳng hàng với `Input` (cũng `px-3`); cỡ `sm` dùng
            //  trong bảng thì giữ `px-2` cho đỡ chật.
            'w-full justify-between gap-1 text-left font-normal',
            size === 'sm' ? 'h-8 px-2 text-sm' : 'px-3',
            wrap ? 'h-auto min-h-8 items-start py-1.5' : 'truncate',
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
              className="shrink-0 transition-colors text-muted-foreground hover:text-foreground"
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

          {/*  NÓI RA phần bị cắt. Danh sách nhân sự lên tới cả nghìn dòng, cắt
               còn 60 mà im lặng thì người dùng cuộn tới đáy, không thấy tên
               mình cần, và kết luận là hệ thống chưa có người đó. */}
          {remaining > 0 && (
            <p className="px-2 py-2 text-center text-xs text-muted-foreground">
              Còn {remaining} mục nữa — gõ để tìm.
            </p>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}
