import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { cn } from '@/shared/utils/cn'
import { nameInitials } from '@/shared/utils/name-initials'
import { pickOrgChartAvatarTone } from '../utils/org-chart-avatar-tone'
import { useOrgChartContext } from '../utils/org-chart-context'
import type { OrgChartPerson } from '../utils/org-chart-forest'

/**
 * Thẻ một người kiểu ERPNext (`EmployeeCard.vue`): vòng chữ viết tắt · tên · chức vụ, bấm để mở khung
 * thông tin. Cao CỐ ĐỊNH 56px (`h-14`) — các đường nối trong `OrgChartTreeNode` đo theo con số này
 * (`top-7` = giữa thẻ), đổi chiều cao thẻ là đường nối lệch.
 */
export function OrgChartPersonCard({ person }: { person: OrgChartPerson }) {
  const { selectedId, meId, select } = useOrgChartContext()
  const selected = selectedId === person.id
  return (
    <button
      type="button"
      data-node={person.id}
      aria-pressed={selected}
      onClick={() => select(person.id)}
      className={cn(
        'flex h-14 w-52 items-center gap-2.5 rounded-lg border px-3 text-left shadow-sm transition-colors',
        selected ? 'border-primary/40 bg-accent' : 'bg-card hover:bg-muted',
      )}
    >
      <Avatar className="size-9">
        <AvatarFallback className={cn('text-xs font-semibold', pickOrgChartAvatarTone(person.id))}>
          {nameInitials(person.fullName)}
        </AvatarFallback>
      </Avatar>
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-1.5">
          <span className="truncate text-sm font-medium" title={person.fullName}>
            {person.fullName}
          </span>
          {person.id === meId && <span className="shrink-0 text-xs text-muted-foreground">Bạn</span>}
        </span>
        {person.position && (
          <span className="block truncate text-xs text-muted-foreground" title={person.position}>
            {person.position}
          </span>
        )}
      </span>
    </button>
  )
}
