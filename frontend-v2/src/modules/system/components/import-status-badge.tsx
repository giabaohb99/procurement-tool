import { Loader2 } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'

import {
  IMPORT_STATUS_DONE,
  IMPORT_STATUS_FAILED,
  IMPORT_STATUS_LABELS,
  IMPORT_STATUS_QUEUED,
  IMPORT_STATUS_RUNNING,
} from '../config/import-meta'

const STATUS_TONES: Record<number, string> = {
  [IMPORT_STATUS_QUEUED]: 'border-slate-300 text-slate-600 bg-slate-50 dark:bg-slate-800',
  [IMPORT_STATUS_DONE]: 'border-emerald-500 text-emerald-600 bg-emerald-50 dark:bg-emerald-950/40',
  [IMPORT_STATUS_FAILED]: 'border-rose-500 text-rose-600 bg-rose-50 dark:bg-rose-950/40',
}

interface ImportStatusBadgeProps {
  status: number
  className?: string
}

/** Badge trạng thái một lần import — dùng chung ở màn danh sách và chi tiết. */
export function ImportStatusBadge({ status, className }: ImportStatusBadgeProps) {
  const label = IMPORT_STATUS_LABELS[status] || `#${status}`

  if (status === IMPORT_STATUS_RUNNING) {
    return (
      <Badge
        variant="outline"
        className={cn('gap-1 border-amber-500 bg-amber-50 text-amber-600 dark:bg-amber-950/40', className)}
      >
        <Loader2 className="size-3 animate-spin" />
        {label}
      </Badge>
    )
  }

  return (
    <Badge
      variant="outline"
      className={cn(STATUS_TONES[status] || 'border-slate-300 text-slate-500 bg-slate-50', className)}
    >
      {label}
    </Badge>
  )
}
