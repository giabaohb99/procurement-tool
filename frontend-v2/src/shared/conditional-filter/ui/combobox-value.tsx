import { ChevronsUpDown, Loader2 } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import { useFilterOptions } from '../hooks/use-filter-options'
import type { FilterFieldDefinition } from '../types'

interface ComboboxValueProps {
  field: FilterFieldDefinition
  value: string
  onChange: (value: string) => void
}

/**
 * Ô chọn một giá trị từ danh sách nạp động (`field.fetchOptions`) — dùng cho cả kiểu
 * `combobox` lẫn kiểu `select` chỉ khai `fetchOptions` (duoc-CR-778).
 *
 * FilterCN gốc dùng `cmdk`; ở đây dựng lại bằng Popover + Input + danh sách
 * nút bấm để khỏi thêm phụ thuộc. Lọc do SERVER làm — mỗi lần gõ là một lần
 * `fetchOptions(query)`, hợp với danh mục vài nghìn dòng như nhân sự.
 */
export function ComboboxValue({ field, value, onChange }: ComboboxValueProps) {
  const [open, setOpen] = useState(false)
  const { options, labels, loading, search } = useFilterOptions(field.fetchOptions)

  //  duoc-CR-778: tra nhãn trong sổ đã nạp chứ không chỉ trong lượt tìm hiện tại — gõ tìm
  //  một chữ khác là mục đang chọn rơi khỏi `options` và ô chỉ còn hiện cái id.
  const selectedLabel = labels[value] || value || 'Chọn giá trị…'

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          role="combobox"
          aria-expanded={open}
          variant="outline"
          className="min-w-40 flex-1 justify-between font-normal"
        >
          <span className="truncate">{selectedLabel}</span>
          <ChevronsUpDown className="opacity-50" />
        </Button>
      </PopoverTrigger>

      <PopoverContent align="start" className="w-64 p-2">
        <Input
          autoFocus
          placeholder="Gõ để tìm…"
          onChange={(e) => search(e.target.value)}
        />

        <div className="mt-2 max-h-52 overflow-y-auto">
          {loading && (
            <p className="flex items-center justify-center gap-2 p-3 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Đang tải…
            </p>
          )}

          {!loading && options.length === 0 && (
            <p className="p-3 text-center text-sm text-muted-foreground">
              Không tìm thấy kết quả.
            </p>
          )}

          {!loading &&
            options.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  onChange(option.value)
                  setOpen(false)
                }}
                className={cn(
                  'block w-full truncate rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent',
                  option.value === value && 'bg-accent font-medium',
                )}
              >
                {option.label}
              </button>
            ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
