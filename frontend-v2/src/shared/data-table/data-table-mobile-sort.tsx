import { ArrowDownNarrowWide, ArrowUpDown, ArrowUpNarrowWide } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from '@/shared/ui/select'

import { columnLabel } from './required-header'
import type { DataTableColumn } from './types'

/** Giá trị của mục "không xếp" — Radix Select cấm `value=""` ở `SelectItem`. */
const NO_SORT = '__none__'

interface DataTableMobileSortProps<T> {
  columns: DataTableColumn<T>[]
  sortBy?: string
  sortDir?: 'asc' | 'desc'
  onSortChange: (sortBy: string, sortDir: 'asc' | 'desc') => void
}

/** Nhãn một cột trong ô chọn: cột thuộc nhóm (Lần 1, Lần 2…) kèm tên nhóm, không thì ba ô "Ngày mua" giống hệt nhau. */
function sortOptionLabel<T>(column: DataTableColumn<T>): string {
  const label = columnLabel(column.header)
  return column.group ? `${column.group} · ${label}` : label
}

/** Danh sách cột xếp được, theo đúng khóa gửi máy chủ (`sortKey ?? key`). */
function listMobileSortOptions<T>(columns: DataTableColumn<T>[]) {
  return columns
    .filter((column) => column.sortable)
    .map((column) => ({
      key: column.sortKey ?? column.key,
      label: sortOptionLabel(column),
      descFirst: Boolean(column.sortDescFirst),
    }))
}

/**
 * Ô "Xếp theo" + nút đổi chiều ở CHẾ ĐỘ THẺ — xem `DataTableProps.mobileSort` (duoc-CR-784).
 *
 * ⚠️ **Vì sao cần.** Ở chế độ thẻ bảng gỡ hẳn hàng tiêu đề, mà bấm tiêu đề là đường DUY NHẤT để xếp. Màn phân trang tại
 * máy chủ thì người dùng điện thoại mất luôn khả năng xem "sản phẩm tăng nhiều nhất" trước — họ chỉ thấy trang 1 theo thứ
 * tự mặc định. Ô chọn này gửi đúng `onSortChange` như tiêu đề cột, nên máy chủ nhận cùng khóa, Xuất Excel cùng thứ tự.
 *
 * Chọn cột = xếp theo chiều ĐẦU của cột đó (cột thời gian / số tiền khai `sortDescFirst` thì giảm trước — cùng luật với
 * cú bấm tiêu đề đầu tiên); nút bên cạnh đảo chiều. Mục "Mặc định" = thôi xếp (khóa rỗng), như nhịp thứ ba của tiêu đề.
 */
export function DataTableMobileSort<T>({
  columns,
  sortBy,
  sortDir = 'asc',
  onSortChange,
}: DataTableMobileSortProps<T>) {
  const options = listMobileSortOptions(columns)
  if (options.length === 0) return null
  const active = options.find((option) => option.key === sortBy)

  return (
    <div className="flex min-w-0 items-center gap-1">
      <Select
        value={active ? active.key : NO_SORT}
        onValueChange={(value) => {
          if (value === NO_SORT) return onSortChange('', 'asc')
          const picked = options.find((option) => option.key === value)
          onSortChange(value, picked?.descFirst ? 'desc' : 'asc')
        }}
      >
        {/*  Ô gọn chỉ có biểu tượng: thanh công cụ khổ điện thoại phải để ô tìm cùng hàng với nó (người chủ chê dải trống
             26/11/2026). Cột đang xếp đọc ở `title` / nhãn đọc màn hình, và nút đổi chiều chỉ hiện khi đang xếp. */}
        <SelectTrigger
          aria-label={active ? `Xếp theo: ${active.label}` : 'Xếp theo'}
          title={active ? `Xếp theo: ${active.label}` : 'Xếp theo'}
          className={cn('h-9 gap-1 px-2', active && 'border-primary text-primary [&_svg]:text-primary')}
        >
          <ArrowUpDown />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={NO_SORT}>Xếp mặc định</SelectItem>
          {options.map((option) => (
            <SelectItem key={option.key} value={option.key}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {active && (
        <Button
          type="button"
          variant="outline"
          size="icon"
          aria-label={sortDir === 'asc' ? 'Đang xếp tăng dần, bấm để xếp giảm dần' : 'Đang xếp giảm dần, bấm để xếp tăng dần'}
          title={sortDir === 'asc' ? 'Tăng dần' : 'Giảm dần'}
          onClick={() => onSortChange(active.key, sortDir === 'asc' ? 'desc' : 'asc')}
        >
          {sortDir === 'asc' ? <ArrowUpNarrowWide /> : <ArrowDownNarrowWide />}
        </Button>
      )}
    </div>
  )
}
