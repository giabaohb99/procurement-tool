import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import { DOSSIER_STATUS, DOSSIER_STATUS_LABEL, type DossierStatus } from '../types/dossier'

/**
 * Màu theo trạng thái. `outline` + lớp màu riêng thay vì `default` cho cả năm:
 * *Sắp hết hạn* và *Hết hạn* là hai thứ người dùng phải nhận ra từ xa, năm huy
 * hiệu cùng màu thì phải đọc chữ từng dòng mới biết hồ sơ nào cần xử lý.
 *
 * Màu dùng biến thể `dark:` vì bậc 600/700 quá tối trên nền tối — cùng luật với
 * `ErpModule.accent`.
 */
const STATUS_CLASS: Record<DossierStatus, string> = {
  [DOSSIER_STATUS.DRAFT]: 'text-muted-foreground',
  [DOSSIER_STATUS.ACTIVE]: 'border-emerald-300 text-emerald-700 dark:text-emerald-400',
  [DOSSIER_STATUS.EXPIRING]: 'border-amber-300 text-amber-700 dark:text-amber-400',
  [DOSSIER_STATUS.EXPIRED]: 'border-destructive/40 text-destructive',
  [DOSSIER_STATUS.ARCHIVED]: 'border-slate-300 text-slate-600 dark:text-slate-400',
}

export function DossierStatusBadge({ status }: { status: DossierStatus }) {
  return (
    <Badge variant="outline" className={cn('font-medium', STATUS_CLASS[status])}>
      {DOSSIER_STATUS_LABEL[status]}
    </Badge>
  )
}
