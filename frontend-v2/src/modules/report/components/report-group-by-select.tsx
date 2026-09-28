import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

import type { ReportDimensionMeta } from '../types/report-analytics'

interface ReportGroupBySelectProps {
  /** `meta.dimensions` trả về từ backend — nguồn DUY NHẤT của danh sách chiều. */
  dimensions: ReportDimensionMeta[]
  value: string
  onChange: (value: string) => void
}

/**
 * Ô "Xem theo" của bảng nhóm — danh sách chiều đọc thẳng từ `meta.dimensions`,
 * không gõ tay: thêm một chiều nhóm mới ở backend là ô này tự có thêm lựa chọn.
 *
 * Gọn: nhãn "Xem theo" đứng NGOÀI ô chọn (không lặp lại trong từng mục như bản
 * cũ) — ô chọn chỉ còn tên chiều, đặt vào `toolbar` của `DataTable` cho vừa một
 * hàng cùng tiêu đề thẻ và menu "Cột" (`ReportGroupedTable`).
 */
export function ReportGroupBySelect({ dimensions, value, onChange }: ReportGroupBySelectProps) {
  if (dimensions.length === 0) return null

  return (
    <div className="flex shrink-0 items-center gap-1.5">
      <span className="text-sm text-muted-foreground">Xem theo</span>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="h-8 w-auto min-w-32 gap-1.5" aria-label="Xem theo">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {dimensions.map((dimension) => (
            <SelectItem key={dimension.key} value={dimension.key}>
              {dimension.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
