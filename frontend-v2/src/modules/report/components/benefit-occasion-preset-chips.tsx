import { useSearchParams } from 'react-router-dom'

import { useSetUrlParams } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'

import {
  BENEFIT_OCCASION_PRESETS,
  buildOccasionPresetParams,
  findActiveOccasionPreset,
} from '../utils/benefit-occasion-presets'

interface BenefitOccasionPresetChipsProps {
  occasionDate: string
  /** Thiếu `employee_sensitive.read` → khóa các dịp lọc theo ngày sinh / tuổi con (backend sẽ trả 403). */
  canUseSensitive: boolean
}

/**
 * Hàng nút «Dịp có sẵn» của H1. Mỗi lần bấm = MỘT lượt ghi URL gồm đủ bộ lọc của dịp + tên
 * dịp (+ ngày dịp với dịp dương lịch cố định) — gọi nhiều setter liên tiếp thì lượt sau đè
 * lượt trước (`useSetUrlParams`).
 */
export function BenefitOccasionPresetChips({ occasionDate, canUseSensitive }: BenefitOccasionPresetChipsProps) {
  const [searchParams] = useSearchParams()
  const setParams = useSetUrlParams()
  const active = findActiveOccasionPreset(searchParams, occasionDate)

  return (
    <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Dịp có sẵn">
      <span className="mr-1 text-sm font-medium">Dịp có sẵn</span>
      {BENEFIT_OCCASION_PRESETS.map((preset) => {
        const isActive = active === preset.id
        return (
          <Button
            key={preset.id}
            type="button"
            size="sm"
            variant={isActive ? 'default' : 'outline'}
            aria-pressed={isActive}
            disabled={preset.needsSensitive && !canUseSensitive}
            onClick={() => setParams(buildOccasionPresetParams(preset, occasionDate))}
          >
            {preset.chip}
          </Button>
        )
      })}
    </div>
  )
}
