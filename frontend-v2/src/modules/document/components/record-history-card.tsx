import { FormCard } from '@/shared/ui/form-card'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import type { HistoryEntry } from '../store/local-collection'

interface RecordHistoryCardProps {
  entries: HistoryEntry[]
}

/**
 * "Lịch sử thao tác" — khối cuối của MỌI trang chi tiết trong phân hệ Văn bản.
 *
 * ⚠️ Dựng lại giao diện của `shared/audit/AuditTimeline` thay vì dùng thẳng nó:
 * component kia gọi `/api/audit-logs`, mà phân hệ này chưa có backend nên chưa
 * có gì để gọi. Khi có endpoint thì bỏ file này, thay bằng
 * `<AuditTimeline entity="…" entityId={id} />`.
 */
export function RecordHistoryCard({ entries }: RecordHistoryCardProps) {
  return (
    <FormCard title="Lịch sử thao tác">
      {entries.length === 0 ? (
        <p className="text-sm text-muted-foreground">Chưa có thao tác nào.</p>
      ) : (
        <ol className="space-y-2.5">
          {entries.map((entry) => (
            <li key={`${entry.at}-${entry.action}`} className="flex gap-3">
              <span
                className={cn('mt-1.5 size-2 shrink-0 rounded-full', dotColor(entry.action))}
              />
              <div className="min-w-0">
                <p className="text-sm">
                  <b>{entry.by}</b> — {entry.action_label}
                  {entry.message ? `: ${entry.message}` : ''}
                </p>
                <p className="text-xs text-muted-foreground">{formatDateTime(entry.at)}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </FormCard>
  )
}

/** Xanh lá = việc thành, đỏ = việc hỏng/hủy, còn lại xanh thương hiệu. */
function dotColor(action: HistoryEntry['action']): string {
  if (action === 'create') return 'bg-emerald-500'
  if (action === 'delete') return 'bg-destructive'
  return 'bg-primary'
}
