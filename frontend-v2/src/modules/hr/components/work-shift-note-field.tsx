import { Textarea } from '@/shared/ui/textarea'

/** Trần `note` của `tab_work_shift_day` (String 255). */
const NOTE_MAX = 255

interface WorkShiftNoteFieldProps {
  value: string
  onChange: (next: string) => void
  readOnly: boolean
}

/** Ô "Ghi chú" của hộp xếp ca: chỉ xem thì là đoạn chữ thường (ẩn khi trống), sửa được thì có bộ đếm ký tự. */
export function WorkShiftNoteField({ value, onChange, readOnly }: WorkShiftNoteFieldProps) {
  if (readOnly) {
    //  Chỉ xem: đoạn chữ thường, không khung; không có ghi chú thì không bày mục này.
    if (!value.trim()) return null
    return (
      <div className="space-y-1">
        <p className="text-sm text-muted-foreground">Ghi chú</p>
        <p className="text-sm break-words whitespace-pre-wrap">{value}</p>
      </div>
    )
  }
  return (
    <div className="space-y-1">
      <label htmlFor="work-shift-note" className="text-sm font-medium">
        Ghi chú
      </label>
      <Textarea
        id="work-shift-note"
        value={value}
        maxLength={NOTE_MAX}
        rows={2}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Vd: Livestream kênh Shopee"
      />
      <p className="text-right text-xs text-muted-foreground tabular-nums">
        {value.length}/{NOTE_MAX}
      </p>
    </div>
  )
}
