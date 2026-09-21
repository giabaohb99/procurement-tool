import { Check } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import {
  currentPhaseKey,
  donePercent,
  isDossierDone,
  type ChecklistGroup,
} from '../../utils/dossier-checklist-helpers'

interface DossierChecklistTrackingProps {
  groups: ChecklistGroup[]
  className?: string
}

/**
 * Cột TIẾN TRÌNH của thẻ thử — chép bố cục `SurveyReportTracking` của khối
 * *Báo cáo thực hiện* để hai thẻ so được với nhau bằng mắt.
 *
 * ⚠️ **Một điểm nháy, không phải nhiều.** Bản gốc cho mỗi nút dòng hàng một
 * track riêng nên có thể nhiều điểm cùng nháy, kèm huy hiệu ghi số nút; ở đây
 * tiến độ là của cả phiếu nên đúng một điểm. Khác biệt có chủ ý — thấy rõ thì
 * mới đánh giá được cái nào hợp hơn.
 *
 * ⚠️ «Xong» = tờ giấy ĐÃ CÓ TRONG KHO, không phải «xong cho phiếu này» — xem
 * ghi chú dài ở `dossier-checklist-helpers.ts`.
 */
export function DossierChecklistTracking({
  groups,
  className,
}: DossierChecklistTrackingProps) {
  if (!groups.length) return null
  const current = currentPhaseKey(groups)

  return (
    <div className={cn('h-fit rounded-lg border bg-muted/20 p-3 lg:sticky lg:top-4', className)}>
      <p className="mb-3 text-xs font-semibold tracking-wider text-muted-foreground uppercase">
        Tiến trình
      </p>
      <ol className="relative space-y-4">
        <span aria-hidden className="absolute top-2 bottom-2 left-[11px] w-px bg-border" />
        {groups.map((group, index) => {
          const doneCount = group.docs.filter(isDossierDone).length
          const done = group.docs.length > 0 && doneCount === group.docs.length
          const active = group.key === current
          return (
            <li key={group.key} className="relative flex items-start gap-2.5">
              <span
                title={active ? 'Đang ở đây' : undefined}
                className={cn(
                  'relative z-10 grid size-6 shrink-0 place-items-center rounded-full border-2 bg-card text-[11px] font-semibold',
                  done
                    ? 'border-success bg-success text-white'
                    : active
                      ? 'border-warning text-warning'
                      : 'border-border text-muted-foreground',
                )}
              >
                {active && (
                  <span
                    aria-hidden
                    className="absolute inset-0 animate-ping rounded-full bg-warning/40"
                  />
                )}
                <span className="relative">
                  {done ? <Check className="size-3.5" /> : index + 1}
                </span>
              </span>
              <div className="min-w-0 pt-0.5">
                <p
                  className={cn(
                    'truncate text-xs font-medium',
                    active ? 'text-foreground' : 'text-muted-foreground',
                  )}
                >
                  {group.name}
                </p>
                <p className="text-[11px] tabular-nums text-muted-foreground">
                  {group.docs.length
                    ? `${doneCount}/${group.docs.length} hồ sơ · ${donePercent(group.docs)}%`
                    : 'Chưa có hồ sơ'}
                </p>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
