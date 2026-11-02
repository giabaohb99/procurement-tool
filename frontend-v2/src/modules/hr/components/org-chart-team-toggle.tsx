import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp } from 'lucide-react'

import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { cn } from '@/shared/utils/cn'
import { nameInitials } from '@/shared/utils/name-initials'
import { pickOrgChartAvatarTone } from '../utils/org-chart-avatar-tone'
import { useOrgChartContext } from '../utils/org-chart-context'
import type { OrgChartPerson } from '../utils/org-chart-forest'

/** Số vòng chữ viết tắt xem trước trên nút khi nhóm đang thu (ERPNext: `TEAM_PREVIEW_SIZE`). */
const TEAM_PREVIEW_SIZE = 3

interface OrgChartTeamToggleProps {
  person: OrgChartPerson
  open: boolean
  /** Nhóm mở ra phía nào của thẻ: `down` dưới thẻ, `right` cạnh phải. */
  direction?: 'down' | 'right'
  className?: string
}

/** Nút «N cấp dưới» treo ở mép thẻ (`TeamToggle.vue`): thu thì hiện ba vòng xem trước + số người. */
export function OrgChartTeamToggle({ person, open, direction = 'down', className }: OrgChartTeamToggleProps) {
  const { forest, toggle } = useOrgChartContext()
  const preview = person.reportIds
    .slice(0, TEAM_PREVIEW_SIZE)
    .map((id) => forest.people.get(id))
    .filter((member): member is OrgChartPerson => Boolean(member))
  const Chevron =
    direction === 'down' ? (open ? ChevronUp : ChevronDown) : open ? ChevronLeft : ChevronRight
  return (
    <button
      type="button"
      onClick={() => toggle(person.id)}
      aria-expanded={open}
      aria-label={`${open ? 'Thu' : 'Mở'} nhóm của ${person.fullName}`}
      className={cn(
        'group flex h-6 items-center gap-1.5 rounded-md border bg-card px-1 text-xs text-foreground/80 transition-colors hover:bg-muted',
        className,
      )}
    >
      {!open && (
        <>
          <span className="flex -space-x-1.5">
            {preview.map((member) => (
              <span key={member.id} className="flex rounded-full bg-card p-0.5 group-hover:bg-muted">
                <Avatar className="size-[18px]">
                  <AvatarFallback className={cn('text-[7px] font-semibold', pickOrgChartAvatarTone(member.id))}>
                    {nameInitials(member.fullName)}
                  </AvatarFallback>
                </Avatar>
              </span>
            ))}
          </span>
          <span className="tabular-nums">{person.reportIds.length}</span>
        </>
      )}
      <Chevron aria-hidden className="size-3.5 text-muted-foreground" />
    </button>
  )
}
