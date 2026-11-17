import { ChevronsUpDown, Loader2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import { useFilterOptions } from '../hooks/use-filter-options'
import type { SelectOption } from '../types'

interface MultiSelectValueProps {
  /** Danh sách tĩnh. Bỏ qua khi có `fetchOptions`. */
  options: SelectOption[]
  selected: string[]
  onChange: (values: string[]) => void
  /**
   * duoc-CR-778: danh sách nạp động, lọc tại SERVER theo từ khóa gõ vào. Trước bản vá
   * này trường chỉ khai `fetchOptions` (Phòng chủ trì, Chức vụ…) chọn operator "thuộc danh
   * sách" là ra hộp rỗng "Không có giá trị nào" vì nhánh này chỉ đọc `field.options`.
   */
  fetchOptions?: (search: string) => Promise<SelectOption[]>
}

/**
 * Ô chọn NHIỀU giá trị cho operator "thuộc danh sách" / "không thuộc danh sách".
 *
 * ⚠️ FilterCN gốc có kiểu trường `multiselect` và operator `in`/`not_in`, nhưng
 * `value-input.tsx` của nó KHÔNG có nhánh nào xử lý — người dùng rơi vào ô text
 * và phải tự gõ chuỗi ngăn cách bằng dấu phẩy. Component này bù chỗ thiếu đó.
 */
export function MultiSelectValue({
  options: staticOptions,
  selected,
  onChange,
  fetchOptions,
}: MultiSelectValueProps) {
  //  Gọi hook vô điều kiện; không có `fetchOptions` thì hook không làm gì.
  const fetched = useFilterOptions(fetchOptions)
  const options = fetchOptions ? fetched.options : staticOptions

  //  Nhãn của mục đã chọn: tra cả sổ nhãn đã nạp — mục chọn từ lượt tìm trước có thể
  //  không còn trong danh sách đang hiện.
  const labelOf = (value: string) =>
    fetched.labels[value] ?? staticOptions.find((option) => option.value === value)?.label ?? value

  const label =
    selected.length === 0
      ? 'Chọn giá trị…'
      : selected.length === 1
        ? labelOf(selected[0])
        : `Đã chọn ${selected.length}`

  const toggle = (value: string) =>
    onChange(
      selected.includes(value)
        ? selected.filter((item) => item !== value)
        : [...selected, value],
    )

  const loading = Boolean(fetchOptions) && fetched.loading

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          type="button"
          role="combobox"
          variant="outline"
          className="min-w-40 flex-1 justify-between font-normal"
        >
          <span className="truncate">{label}</span>
          <ChevronsUpDown className="opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className={cn('p-1', fetchOptions ? 'w-64' : 'w-56')}>
        {fetchOptions && (
          <div className="p-1">
            <Input
              autoFocus
              placeholder="Gõ để tìm…"
              onChange={(event) => fetched.search(event.target.value)}
            />
          </div>
        )}
        <div className="max-h-60 overflow-y-auto">
          {loading && (
            <p className="flex items-center justify-center gap-2 p-3 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Đang tải…
            </p>
          )}
          {!loading && options.length === 0 && (
            <p className="p-2 text-sm text-muted-foreground">Không có giá trị nào.</p>
          )}
          {!loading &&
            options.map((option) => (
              <label
                key={option.value}
                className="flex cursor-pointer items-center gap-2 rounded-sm transition-colors px-2 py-1.5 text-sm hover:bg-accent"
              >
                <Checkbox
                  checked={selected.includes(option.value)}
                  onCheckedChange={() => toggle(option.value)}
                />
                <span className="truncate">{option.label}</span>
              </label>
            ))}
        </div>
      </PopoverContent>
    </Popover>
  )
}
