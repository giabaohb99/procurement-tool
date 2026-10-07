import { Button } from '@/shared/ui/button'
import { endDateForPreset, termPresetsFor } from '../utils/labor-contract-term-presets'

interface LaborContractTermPresetsProps {
  contractType: number
  startDate: string
  endDate: string
  onPick: (endDate: string) => void
}

/**
 * Hàng nút «12 tháng · 24 tháng · 36 tháng» (thử việc: «30 ngày · 60 ngày») dưới ô Ngày kết thúc.
 * Bấm là điền ngày kết thúc tính từ ngày bắt đầu; nút trùng ngày đang chọn được tô đậm.
 * Chưa có ngày bắt đầu thì nút tắt kèm lời nhắc — điền đại một ngày là sai còn tệ hơn không điền.
 */
export function LaborContractTermPresets({ contractType, startDate, endDate, onPick }: LaborContractTermPresetsProps) {
  const presets = termPresetsFor(contractType)
  if (presets.length === 0) return null
  const hasStart = endDateForPreset(startDate, presets[0]) !== ''
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="text-xs text-muted-foreground">Chọn nhanh:</span>
      {presets.map((preset) => {
        const value = endDateForPreset(startDate, preset)
        const active = hasStart && value === endDate
        return (
          <Button
            key={preset.label}
            //  Nằm trong <form> của hộp HĐ (và form hồ sơ phía ngoài) — thiếu type là bấm thành submit.
            type="button"
            size="xs"
            variant={active ? 'default' : 'outline'}
            aria-pressed={active}
            disabled={!hasStart}
            onClick={() => onPick(value)}
          >
            {preset.label}
          </Button>
        )
      })}
      {!hasStart && <span className="text-xs text-muted-foreground">Chọn ngày bắt đầu trước</span>}
    </div>
  )
}
