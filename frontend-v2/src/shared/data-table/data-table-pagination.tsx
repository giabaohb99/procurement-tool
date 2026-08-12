import { ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { PAGE_ELLIPSIS, getPageItems } from './page-range'
import type { DataTablePagination as PaginationProps } from './types'

/** Số dòng/trang cho người dùng chọn. */
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const

/**
 * Chân bảng: bên TRÁI chọn số dòng mỗi trang + tổng số bản ghi,
 * bên PHẢI là dãy nút số trang kèm lùi/tiến.
 */
export function DataTablePagination({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
  unitLabel,
}: PaginationProps) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  const pageItems = getPageItems(page, pageCount)

  return (
    // Không kẻ `border-t`: bảng phía trên đã có khung viền riêng, thêm vạch nữa
    // là thành hai đường sát nhau. `shrink-0` để khi bảng fit chiều cao thì
    // thanh này không bị bóp lại.
    <div className="mt-3 flex shrink-0 flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>Hiển thị</span>
        <Select
          value={String(pageSize)}
          onValueChange={(value) => {
            onPageSizeChange(Number(value))
            // Đổi cỡ trang thì số trang đổi theo; đang ở trang 7 mà chuyển sang
            // 100 dòng/trang là rơi vào vùng trống.
            onPageChange(1)
          }}
        >
          <SelectTrigger size="sm" className="w-20">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PAGE_SIZE_OPTIONS.map((option) => (
              <SelectItem key={option} value={String(option)}>
                {option}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span>
          dòng · Tổng {total.toLocaleString('vi-VN')} {unitLabel}
        </span>
      </div>

      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon-sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          aria-label="Trang trước"
        >
          <ChevronLeft />
        </Button>

        {pageItems.map((item, index) =>
          item === PAGE_ELLIPSIS ? (
            // Dấu "…" không bấm được nên key theo vị trí là đủ (tối đa 2 cái).
            <span
              key={`gap-${index}`}
              aria-hidden
              className="px-1 text-sm text-muted-foreground"
            >
              …
            </span>
          ) : (
            <Button
              key={item}
              variant={item === page ? 'default' : 'outline'}
              size="icon-sm"
              className="tabular-nums"
              aria-label={`Trang ${item}`}
              aria-current={item === page ? 'page' : undefined}
              onClick={() => onPageChange(item)}
            >
              {item}
            </Button>
          ),
        )}

        <Button
          variant="outline"
          size="icon-sm"
          disabled={page >= pageCount}
          onClick={() => onPageChange(page + 1)}
          aria-label="Trang sau"
        >
          <ChevronRight />
        </Button>
      </div>
    </div>
  )
}
