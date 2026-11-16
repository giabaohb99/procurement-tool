import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { formatHourLabel } from '../utils/work-shift-hours'
import { endHourOptions, START_HOUR_OPTIONS } from '../utils/work-shift-rows'

interface WorkShiftHourRangeInputProps {
  /** "Khung 1" — tiền tố tên hai ô chọn ("Khung 1 — từ giờ"). */
  label: string
  start: number
  end: number
  invalid: boolean
  describedBy?: string
  onStartChange: (hour: number) => void
  onEndChange: (hour: number) => void
}

/**
 * Ô ghép "Từ – Đến" của một khung giờ (duoc-CR-761): MỘT khung viền chứa hai ô chọn shadcn, giữa là gạch nối. Giờ
 * tròn 24 giờ, nhãn đủ "HH:MM"; ô "Đến" chỉ có giờ SAU "Từ" (tới 24:00). Viền đỏ khi dòng sai, vòng sáng khi đang chọn.
 */
export function WorkShiftHourRangeInput({
  label,
  start,
  end,
  invalid,
  describedBy,
  onStartChange,
  onEndChange,
}: WorkShiftHourRangeInputProps) {
  return (
    <div
      role="group"
      aria-label={label}
      aria-invalid={invalid}
      className="flex h-9 w-full items-center rounded-md border border-input bg-background shadow-xs transition-[color,box-shadow] focus-within:border-ring focus-within:ring-[3px] focus-within:ring-ring/50 aria-invalid:border-destructive aria-invalid:ring-destructive/20 md:w-auto dark:bg-input/30"
    >
      <HourSelect
        ariaLabel={`${label} — từ giờ`}
        value={start}
        options={START_HOUR_OPTIONS}
        invalid={invalid}
        describedBy={describedBy}
        onChange={onStartChange}
      />
      <span aria-hidden className="px-0.5 text-muted-foreground">
        –
      </span>
      <HourSelect
        ariaLabel={`${label} — đến giờ`}
        value={end}
        options={endHourOptions(start)}
        invalid={invalid}
        describedBy={describedBy}
        onChange={onEndChange}
      />
    </div>
  )
}

interface HourSelectProps {
  ariaLabel: string
  value: number
  options: readonly number[]
  invalid: boolean
  describedBy?: string
  onChange: (hour: number) => void
}

/** Một ô chọn giờ không viền riêng (viền nằm ở khung ghép bên ngoài); danh sách cuộn, cao tối đa ~15rem. */
function HourSelect({ ariaLabel, value, options, invalid, describedBy, onChange }: HourSelectProps) {
  return (
    <Select value={String(value)} onValueChange={(v) => onChange(Number(v))}>
      <SelectTrigger
        aria-label={ariaLabel}
        aria-invalid={invalid}
        aria-describedby={describedBy}
        className="h-full flex-1 border-0 bg-transparent px-2.5 tabular-nums shadow-none focus-visible:ring-0 aria-invalid:ring-0 md:w-[5.75rem] md:flex-none dark:bg-transparent dark:hover:bg-transparent"
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent className="max-h-[min(var(--radix-select-content-available-height),15rem)]">
        {options.map((h) => (
          <SelectItem key={h} value={String(h)} className="tabular-nums">
            {formatHourLabel(h)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
