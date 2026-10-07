import { Badge } from '@/shared/ui/badge'
import { CONTRACT_STATUS, contractStatusLabel } from '../utils/labor-contract-rules'

/** Sắc thái theo nhóm (cùng thang màu `leave-status-badge`): nháp/hủy trung tính, hiệu lực xanh, hết hạn hổ phách, chấm dứt đỏ. */
const TONES: Record<number, string> = {
  [CONTRACT_STATUS.DRAFT]:
    'border-zinc-300 bg-zinc-100 text-zinc-600 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-300',
  [CONTRACT_STATUS.SIGNED]:
    'border-emerald-300 bg-emerald-100 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950 dark:text-emerald-200',
  [CONTRACT_STATUS.EXPIRED]:
    'border-amber-300 bg-amber-100 text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200',
  [CONTRACT_STATUS.TERMINATED]:
    'border-destructive/40 bg-destructive/15 text-destructive dark:bg-destructive/25',
  [CONTRACT_STATUS.CANCELLED]:
    'border-zinc-400 bg-zinc-200 text-zinc-700 dark:border-zinc-500 dark:bg-zinc-700 dark:text-zinc-200',
}

/** Truyền `effective_status` (có «Hết hạn» suy ra), không phải `status` lưu trong DB. */
export function LaborContractStatusBadge({ status }: { status: number }) {
  return (
    <Badge variant="outline" className={TONES[status] ?? TONES[CONTRACT_STATUS.DRAFT]}>
      {contractStatusLabel(status)}
    </Badge>
  )
}
