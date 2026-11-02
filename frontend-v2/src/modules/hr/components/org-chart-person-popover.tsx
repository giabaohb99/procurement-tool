import { ArrowUpRight, Building2, GitFork, IdCard, Users, X } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { cn } from '@/shared/utils/cn'
import { nameInitials } from '@/shared/utils/name-initials'
import { pickOrgChartAvatarTone } from '../utils/org-chart-avatar-tone'
import { useOrgChartContext } from '../utils/org-chart-context'
import type { OrgChartPerson } from '../utils/org-chart-forest'

interface OrgChartPersonPopoverProps {
  person: OrgChartPerson
  onClose: () => void
  /** Bấm tên quản lý: có thẻ trên sơ đồ thì nhảy tới, không thì mở hồ sơ. */
  onShowManager: (managerId: number) => void
}

/** Khung thông tin nhanh cạnh thẻ đang chọn (`EmployeePopover.vue`): phòng · cấp dưới · quản lý · mở hồ sơ. */
export function OrgChartPersonPopover({ person, onClose, onShowManager }: OrgChartPersonPopoverProps) {
  const { forest, expanded, meId, toggle } = useOrgChartContext()
  const manager = person.managerId ? forest.people.get(person.managerId) : undefined
  const reports = person.reportIds.length
  const teamOpen = expanded.has(person.id)
  return (
    <div className="w-72 rounded-xl border bg-popover p-4 text-popover-foreground shadow-lg">
      <div className="flex items-start gap-3">
        <Avatar className="size-12 shrink-0">
          <AvatarFallback className={cn('font-semibold', pickOrgChartAvatarTone(person.id))}>
            {nameInitials(person.fullName)}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate font-semibold">{person.fullName}</span>
            {person.id === meId && <span className="shrink-0 text-sm text-muted-foreground">Bạn</span>}
          </div>
          {person.position && <p className="mt-0.5 truncate text-sm text-muted-foreground">{person.position}</p>}
        </div>
        <Button type="button" variant="ghost" size="icon-sm" className="-mt-1.5 -mr-1.5" aria-label="Đóng" onClick={onClose}>
          <X />
        </Button>
      </div>

      <dl className="mt-3 space-y-1.5 text-sm">
        <div className="flex items-center gap-2">
          <dt aria-label="Mã nhân sự">
            <IdCard className="size-4 text-muted-foreground" />
          </dt>
          <dd className="min-w-0 truncate">{person.code}</dd>
        </div>
        <div className="flex items-center gap-2">
          <dt aria-label="Phòng ban">
            <Building2 className="size-4 text-muted-foreground" />
          </dt>
          <dd className="min-w-0 truncate">{person.departmentName || 'Chưa gắn phòng ban'}</dd>
        </div>
        {reports > 0 && (
          <div className="flex items-center gap-2">
            <dt aria-label="Cấp dưới">
              <Users className="size-4 text-muted-foreground" />
            </dt>
            <dd>{reports} cấp dưới trực tiếp</dd>
          </div>
        )}
        {manager && (
          <div className="flex items-center gap-2">
            <dt aria-label="Quản lý trực tiếp">
              <ArrowUpRight className="size-4 text-muted-foreground" />
            </dt>
            <dd className="min-w-0">
              <button
                type="button"
                onClick={() => onShowManager(manager.id)}
                className="inline-flex max-w-full items-center gap-2 align-middle"
              >
                <Avatar className="size-5 shrink-0">
                  <AvatarFallback className={cn('text-[9px] font-semibold', pickOrgChartAvatarTone(manager.id))}>
                    {nameInitials(manager.fullName)}
                  </AvatarFallback>
                </Avatar>
                <span className="truncate underline-offset-2 hover:underline">{manager.fullName}</span>
              </button>
            </dd>
          </div>
        )}
      </dl>

      <div className="mt-4 flex items-center gap-2">
        <Button asChild className="flex-1">
          <Link to={appRoutes.hr.employeeDetail(person.id)}>Mở hồ sơ</Link>
        </Button>
        {reports > 0 && (
          <IconTooltip label={teamOpen ? 'Thu nhóm' : 'Mở nhóm'}>
            <Button
              type="button"
              variant="outline"
              size="icon"
              aria-label={teamOpen ? 'Thu nhóm' : 'Mở nhóm'}
              aria-pressed={teamOpen}
              onClick={() => toggle(person.id)}
            >
              <GitFork />
            </Button>
          </IconTooltip>
        )}
      </div>
    </div>
  )
}
