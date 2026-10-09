import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import {
  REPORT_DOC_DONE,
  REPORT_DOC_STATUS_LABELS,
  type SurveyReportDoc,
} from '../../types/survey-request-report'

//  Màu pill theo mã trạng thái hồ sơ (0..3). Dải màu ở MÉP TRÁI mỗi dòng đã bỏ
//  (12/09/2026): trạng thái đã nói bằng ô tick và bằng chữ trên pill, thêm một
//  cột màu nữa chỉ là nhiễu — mắt đọc dải màu trước cả tiêu đề hồ sơ.
const STATUS_PILL: Record<number, string> = {
  0: 'bg-muted text-muted-foreground',
  1: 'bg-warning/15 text-warning',
  2: 'bg-primary/10 text-primary',
  3: 'bg-success/15 text-success',
}

interface ReportDocStatusSelectProps {
  doc: SurveyReportDoc
  /** Hồ sơ đang chờ tiên quyết — không chọn được «Hoàn thành», cùng luật với nút ✓. */
  locked: boolean
  /** Không có quyền sửa: chỉ bày pill chữ, không có ô chọn. */
  readOnly: boolean
  disabled?: boolean
  onChange: (status: number) => void
  className?: string
}

/**
 * Trạng thái hồ sơ NGAY TRÊN DÒNG — ô chọn nhỏ mang màu pill để liếc vẫn đọc được
 * trạng thái (bao-CR-602). Dùng chung cho dòng hồ sơ 2 tầng và dạng «Bảng»
 * (duoc-CR-612) để hai nơi không lệch màu / lệch luật khóa.
 */
export function ReportDocStatusSelect({
  doc,
  locked,
  readOnly,
  disabled = false,
  onChange,
  className,
}: ReportDocStatusSelectProps) {
  const pill = STATUS_PILL[doc.status] ?? STATUS_PILL[0]
  if (readOnly) {
    return (
      <span
        className={cn(
          'shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-semibold whitespace-nowrap',
          pill,
          className,
        )}
      >
        {doc.status_label}
      </span>
    )
  }
  return (
    <Select
      value={String(doc.status)}
      onValueChange={(value) => {
        //  `''` (ca lạ của Radix) mà đọc thành số là 0 = «Chưa bắt đầu» — lặng lẽ mở lại hồ sơ.
        if (!value) return
        const next = Number(value)
        if (next !== doc.status) onChange(next)
      }}
      disabled={disabled}
    >
      <SelectTrigger
        size="sm"
        aria-label={`Trạng thái hồ sơ "${doc.title}"`}
        className={cn(
          'h-6 shrink-0 gap-1 rounded-full border-0 px-2.5 text-[11px] font-semibold shadow-none',
          pill,
          className,
        )}
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent align="end">
        {Object.entries(REPORT_DOC_STATUS_LABELS).map(([code, label]) => (
          <SelectItem key={code} value={code} disabled={locked && Number(code) === REPORT_DOC_DONE}>
            {label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
