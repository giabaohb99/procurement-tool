import { Search } from 'lucide-react'
import type { ReactNode } from 'react'

import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { ALL_OPTION } from '../utils/filter-leave-rows'

interface LeaveRowsFilterBarProps {
  keyword: string
  onKeywordChange: (value: string) => void
  typeId: string
  onTypeChange: (value: string) => void
  /** Loại nghỉ có mặt trong danh sách — xem `leaveTypesIn`. */
  types: { id: number; name: string }[]
  /** Chỗ nhét thêm ô lọc riêng của từng màn (trạng thái, đếm đầu người…). */
  children?: ReactNode
}

/**
 * Thanh TÌM + LỌC dùng chung cho những bảng đơn nghỉ lọc ở phía màn hình.
 *
 * Ba màn xài nó: tab «Cần tôi duyệt», tab «Tôi đã duyệt», và chế độ NGÀY của
 * Lịch nghỉ. Chép ba bản thì ba nơi trôi khác nhau về câu gợi ý, bề rộng ô, và
 * cả cách xử lý loại nghỉ trùng.
 *
 * ⚠️ Ô loại nghỉ TỰ ẨN khi danh sách chỉ có một loại: một ô chọn có đúng một
 * lựa chọn thật không lọc được gì, nó chỉ chiếm chỗ và mời người ta bấm vào để
 * rồi không thấy gì đổi.
 */
export function LeaveRowsFilterBar({
  keyword,
  onKeywordChange,
  typeId,
  onTypeChange,
  types,
  children,
}: LeaveRowsFilterBarProps) {
  return (
    <>
      <div className="relative min-w-56 flex-1 md:max-w-xs">
        <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="Tìm theo tên, số đơn hoặc lý do…"
          value={keyword}
          onChange={(e) => onKeywordChange(e.target.value)}
        />
      </div>

      {types.length > 1 && (
        <Select value={typeId} onValueChange={onTypeChange}>
          <SelectTrigger className="w-44" aria-label="Lọc theo loại nghỉ">
            <SelectValue placeholder="Loại nghỉ" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_OPTION}>Tất cả loại nghỉ</SelectItem>
            {types.map((t) => (
              <SelectItem key={t.id} value={String(t.id)}>
                {t.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {children}
    </>
  )
}
