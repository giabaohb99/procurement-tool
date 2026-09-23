// bao-CR-470 — huy hiệu trạng thái một lô nạp dữ liệu hải quan (dùng ở hộp thoại Nạp dữ
// liệu và Lịch sử nạp). Màu theo bảng tông chung `status-tone.ts`.
import { Badge } from '@/shared/ui/badge'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'

import { CUSTOMS_BATCH_STATUS, type CustomsImportBatch } from '../../types/customs'
import { formatBatchStatus } from '../../utils/customs'

function toneOf(status: number): string {
  if (status === CUSTOMS_BATCH_STATUS.reverted) return TONE_CLASS.neutral
  if (status === CUSTOMS_BATCH_STATUS.failed) return TONE_CLASS.danger
  if (status === CUSTOMS_BATCH_STATUS.done) return TONE_CLASS.done
  return TONE_CLASS.progress
}

export function CustomsBatchStatusBadge({ batch }: { batch: Pick<CustomsImportBatch, 'mode' | 'status'> }) {
  return <Badge className={cn(toneOf(batch.status))}>{formatBatchStatus(batch)}</Badge>
}
