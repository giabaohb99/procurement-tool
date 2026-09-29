// Nhãn tình trạng đăng ký của một thuốc BVTV (mục «Thuốc BVTV» của Tra cứu thị trường).
import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'

import { PESTICIDE_STATUS } from '../../types/customs-pesticide'

/** Còn hiệu lực = xanh (dùng được) · Hết hiệu lực = đỏ · Đang sử dụng = xanh dương (nhóm cũ, không hạn). */
const STATUS_TONE: Record<number, string> = {
  [PESTICIDE_STATUS.active]: TONE_CLASS.done,
  [PESTICIDE_STATUS.expired]: TONE_CLASS.danger,
  [PESTICIDE_STATUS.inUse]: TONE_CLASS.progress,
}

export function CustomsPesticideStatusBadge({ status, label }: { status: number; label: string }) {
  if (!label) return null
  return (
    <Badge variant="secondary" className={cn('font-medium', STATUS_TONE[status] ?? TONE_CLASS.neutral)}>
      {label}
    </Badge>
  )
}
