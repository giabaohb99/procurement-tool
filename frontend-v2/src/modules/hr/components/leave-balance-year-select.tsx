import { useMemo } from 'react'

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

//  Bao nhiêu năm bày ra ô chọn. Quỹ phép không tra ngược quá vài năm — cần xa
//  hơn thì đó là việc của báo cáo, không phải màn thao tác hằng ngày.
const YEAR_SPAN = 3

interface LeaveBalanceYearSelectProps {
  value: string
  onChange: (year: string) => void
}

/**
 * Ô chọn NĂM của màn Quỹ phép — dùng chung cho thẻ "Theo dòng quỹ" và "Theo nhân sự" (cùng tham số
 * URL `year`, nên đổi thẻ vẫn giữ năm đang xem).
 *
 * Ô CHỌN chứ không phải ô nhập số: ô số cho gõ "20226" hay "0" và bảng lập tức rỗng không rõ vì
 * sao, lại còn có mũi tên tăng giảm chạy từng năm một. Năm sau cũng có mặt (cấp quỹ trước Tết).
 */
export function LeaveBalanceYearSelect({ value, onChange }: LeaveBalanceYearSelectProps) {
  const currentYear = new Date().getFullYear()
  const years = useMemo(
    () => Array.from({ length: YEAR_SPAN + 1 }, (_, i) => String(currentYear + 1 - i)),
    [currentYear],
  )
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-full md:w-32" aria-label="Chọn năm">
        <SelectValue placeholder="Năm" />
      </SelectTrigger>
      <SelectContent>
        {years.map((y) => (
          <SelectItem key={y} value={y}>
            Năm {y}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
