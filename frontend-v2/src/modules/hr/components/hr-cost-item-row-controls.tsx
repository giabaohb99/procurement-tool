import { ArrowDown, ArrowUp, Trash2 } from 'lucide-react'

import type { StatusOption } from '@/shared/constants/statuses'
import { Button } from '@/shared/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

/** Ô chọn theo một bộ mã số do `gen_status_ts.py` sinh (cách tính, áp cho, nguồn thực tế). */
export function CodeSelect({
  value,
  options,
  label,
  onChange,
}: {
  value: number
  options: readonly StatusOption[]
  label: string
  onChange: (v: number) => void
}) {
  return (
    <Select value={String(value)} onValueChange={(v) => onChange(Number(v))}>
      <SelectTrigger className="h-auto min-h-9 w-full whitespace-normal text-left" aria-label={label}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

interface HrCostItemRowActionsProps {
  label: string
  isFirst: boolean
  isLast: boolean
  onMove: (delta: -1 | 1) => void
  onRemove: () => void
}

/**
 * Lên · Xuống · Bỏ khoản. Đổi thứ tự bằng nút thay vì kéo thả dòng: `LinesTable` kéo CỘT chứ không
 * kéo dòng, và nút bấm được cả bằng bàn phím lẫn trên điện thoại.
 */
export function HrCostItemRowActions({ label, isFirst, isLast, onMove, onRemove }: HrCostItemRowActionsProps) {
  return (
    <div className="flex items-center gap-0.5">
      <Button type="button" variant="ghost" size="icon" className="size-7" title="Lên" aria-label={`Đưa ${label} lên`} disabled={isFirst} onClick={() => onMove(-1)}>
        <ArrowUp className="size-4" />
      </Button>
      <Button type="button" variant="ghost" size="icon" className="size-7" title="Xuống" aria-label={`Đưa ${label} xuống`} disabled={isLast} onClick={() => onMove(1)}>
        <ArrowDown className="size-4" />
      </Button>
      <Button type="button" variant="ghost" size="icon" className="size-7 text-destructive" title="Bỏ khoản" aria-label={`Bỏ khoản ${label}`} onClick={onRemove}>
        <Trash2 className="size-4" />
      </Button>
    </div>
  )
}
