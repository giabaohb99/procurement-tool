import { Building2, CalendarDays } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import { nameInitials } from '@/shared/utils/name-initials'
import type { ConcurrentMember } from '../types/concurrent-member'
import { formatConcurrentPeriod, formatPrimaryPlace } from '../utils/concurrent-member-display'
import { pickOrgChartAvatarTone } from '../utils/org-chart-avatar-tone'
import { concurrentGroupTitle, type OrgChartConcurrentGroup } from '../utils/org-chart-forest'

/**
 * Người KIÊM NHIỆM trên sơ đồ tổ chức (duoc-CR-755), vẽ dưới cây quản lý theo từng nơi kiêm nhiệm: nhóm phòng
 * (*Phòng X — Công ty A*) cho dòng loại Phòng ban, nhóm *Kiêm nhiệm tại công ty B* cho dòng loại Công ty (duoc-CR-756).
 *
 * Thẻ viền NÉT ĐỨT + huy hiệu **Kiêm nhiệm** để không ai nhầm với nhân sự thuộc phòng. Không có cạnh quản lý trực
 * tiếp: cạnh đó thuộc vị trí chính của người ấy (ở công ty / phòng chính), vẽ thêm ở đây là nói sai tổ chức.
 * Chi tiết (phòng + công ty chính, thời hạn, mở hồ sơ) mở NGAY DƯỚI thẻ chứ không bằng cửa sổ nổi: khung sơ đồ
 * kéo-thả và phóng to nên cửa sổ nổi tách khỏi nó sẽ trôi lệch khi người dùng kéo.
 */
export function OrgChartConcurrentSection({
  groups,
  truncated = false,
}: {
  groups: OrgChartConcurrentGroup[]
  /** Backend đã cắt danh sách ở trần dòng — báo một dòng chú thích để không ai tin sơ đồ là đủ. */
  truncated?: boolean
}) {
  const [openId, setOpenId] = useState<number | null>(null)
  if (groups.length === 0) return null

  return (
    <section aria-label="Người kiêm nhiệm" className="mt-12 flex max-w-4xl flex-col items-center gap-5">
      <h3 className="text-sm font-semibold text-muted-foreground">Kiêm nhiệm tại các phòng và công ty đang xem</h3>
      {truncated && (
        <p role="note" className="text-xs text-muted-foreground">
          Sơ đồ chỉ hiện phần đầu danh sách kiêm nhiệm (xếp theo họ tên); còn một số người chưa được vẽ ở đây.
        </p>
      )}
      {groups.map((group) => (
        <div key={group.key} className="flex flex-col items-center gap-2">
          <p className="text-xs font-medium text-muted-foreground">{concurrentGroupTitle(group)}</p>
          <div className="flex flex-wrap justify-center gap-3">
            {group.members.map((member) => (
              <ConcurrentCard
                key={member.id}
                member={member}
                open={openId === member.id}
                onToggle={() => setOpenId((current) => (current === member.id ? null : member.id))}
              />
            ))}
          </div>
        </div>
      ))}
    </section>
  )
}

function ConcurrentCard({ member, open, onToggle }: { member: ConcurrentMember; open: boolean; onToggle: () => void }) {
  const primary = formatPrimaryPlace(member)
  return (
    <div className="flex w-52 flex-col gap-1.5">
      <button
        type="button"
        aria-expanded={open}
        onClick={onToggle}
        className={cn(
          'flex h-14 w-52 items-center gap-2.5 rounded-lg border border-dashed px-3 text-left shadow-sm transition-colors',
          open ? 'border-primary/50 bg-accent' : 'bg-card hover:bg-muted',
        )}
      >
        <Avatar className="size-9">
          <AvatarFallback className={cn('text-xs font-semibold', pickOrgChartAvatarTone(member.employee_id))}>
            {nameInitials(member.full_name)}
          </AvatarFallback>
        </Avatar>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-medium" title={member.full_name}>
            {member.full_name}
          </span>
          <span className="flex items-center gap-1.5">
            <Badge variant="outline" className="shrink-0 px-1.5 py-0 text-[10px]">
              Kiêm nhiệm
            </Badge>
            {member.position_label && (
              <span className="truncate text-xs text-muted-foreground" title={member.position_label}>
                {member.position_label}
              </span>
            )}
          </span>
        </span>
      </button>

      {open && (
        <dl className="space-y-1 rounded-lg border bg-popover p-3 text-xs text-popover-foreground shadow-sm">
          <div className="flex items-start gap-2">
            <dt aria-label="Thuộc phòng chính">
              <Building2 className="mt-0.5 size-3.5 text-muted-foreground" />
            </dt>
            <dd className="min-w-0 break-words">
              <span className="text-muted-foreground">Thuộc: </span>
              {primary || 'Chưa rõ phòng chính'}
            </dd>
          </div>
          <div className="flex items-start gap-2">
            <dt aria-label="Hiệu lực">
              <CalendarDays className="mt-0.5 size-3.5 text-muted-foreground" />
            </dt>
            <dd>{formatConcurrentPeriod(member.from_date, member.to_date)}</dd>
          </div>
          {member.can_open ? (
            <Link
              to={appRoutes.hr.employeeDetail(member.employee_id)}
              className="inline-block pt-1 font-medium text-primary underline-offset-2 hover:underline"
            >
              Mở hồ sơ
            </Link>
          ) : (
            <p className="pt-1 text-muted-foreground">Bạn chỉ xem được dòng kiêm nhiệm này, không mở được hồ sơ.</p>
          )}
        </dl>
      )}
    </div>
  )
}
