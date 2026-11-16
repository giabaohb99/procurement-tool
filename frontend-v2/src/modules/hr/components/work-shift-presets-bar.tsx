import { Button } from '@/shared/ui/button'
import { OFFICE_HOURS_PRESET, type TemplateRanges } from '../utils/work-shift-hours'

interface WorkShiftPresetsBarProps {
  /** Khung của mẫu tuần ngày đó; `null` = chưa đọc được (nút "Theo lịch tuần" tắt). */
  template: TemplateRanges | null
  /** Thay CẢ danh sách khung; `rounded` = mẫu có giờ lẻ đã làm tròn (hộp hiện câu nhắc). */
  onApply: (ranges: readonly (readonly number[])[], rounded?: boolean) => void
}

/** Hàng "Mẫu nhanh" của hộp xếp ca (duoc-CR-761): Theo lịch tuần · Hành chính 08–17 · Nghỉ cả ngày. */
export function WorkShiftPresetsBar({ template, onApply }: WorkShiftPresetsBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-sm text-muted-foreground">Mẫu nhanh:</span>
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={!template}
        title={template ? undefined : 'Chưa đọc được mẫu lịch tuần của ngày này'}
        onClick={() => template && onApply(template.ranges, template.rounded)}
      >
        Theo lịch tuần
      </Button>
      <Button type="button" variant="outline" size="sm" onClick={() => onApply(OFFICE_HOURS_PRESET)}>
        Hành chính 08–17
      </Button>
      <Button type="button" variant="outline" size="sm" onClick={() => onApply([])}>
        Nghỉ cả ngày
      </Button>
    </div>
  )
}
