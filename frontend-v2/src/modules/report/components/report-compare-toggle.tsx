import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group'

import type { ReportCompareMode } from '../types/report-analytics'

const OPTIONS: { value: ReportCompareMode; label: string }[] = [
  { value: 'previous', label: 'Kỳ trước' },
  { value: 'year', label: 'Cùng kỳ năm trước' },
  { value: 'none', label: 'Không so sánh' },
]

interface ReportCompareToggleProps {
  value: ReportCompareMode
  onChange: (value: ReportCompareMode) => void
}

/**
 * Thanh "So sánh với" — nút BA lựa chọn (segmented control), thay ô Select cũ:
 * chỉ ba giá trị cố định thì bày sẵn cả ba đỡ một cú bấm mở/đóng hơn ô chọn.
 * Dùng bên trong popover kỳ (`ReportPeriodControl`), đổi giá trị chỉ cập nhật
 * bản NHÁP cục bộ — chưa ghi lên URL cho tới khi bấm "Áp dụng".
 */
export function ReportCompareToggle({ value, onChange }: ReportCompareToggleProps) {
  return (
    <ToggleGroup
      type="single"
      variant="outline"
      value={value}
      onValueChange={(next) => next && onChange(next as ReportCompareMode)}
      className="w-full"
    >
      {OPTIONS.map((option) => (
        <ToggleGroupItem
          key={option.value}
          value={option.value}
          className="flex-1 text-xs sm:text-sm"
        >
          {option.label}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  )
}
