// bao-CR-718 — huy hiệu trạng thái một lô XUẤT toàn bộ (khác `customs-batch-status-badge` của lô NẠP).
// Nhãn lấy thẳng `status_label` của backend (bộ mã chưa vào sổ sinh tự động `statuses.ts`); màu theo
// bảng tông chung `status-tone.ts`.
import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'

import { CUSTOMS_EXPORT_STATUS, type CustomsExportBatch } from '../../types/customs'

function toneOf(status: number): string {
  switch (status) {
    case CUSTOMS_EXPORT_STATUS.queued:
      return TONE_CLASS.pending
    case CUSTOMS_EXPORT_STATUS.running:
      return TONE_CLASS.progress
    case CUSTOMS_EXPORT_STATUS.done:
      return TONE_CLASS.done
    case CUSTOMS_EXPORT_STATUS.failed:
      return TONE_CLASS.danger
    case CUSTOMS_EXPORT_STATUS.cancelled:
      return TONE_CLASS.returned
    default:
      return TONE_CLASS.neutral
  }
}

export function CustomsExportStatusBadge({ batch }: { batch: Pick<CustomsExportBatch, 'status' | 'status_label'> }) {
  return (
    <Badge className={cn(toneOf(batch.status))}>{batch.status_label || `Trạng thái ${batch.status}`}</Badge>
  )
}
