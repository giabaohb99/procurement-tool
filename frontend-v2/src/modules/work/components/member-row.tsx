import { Crown, UserMinus } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { WORK_ROLE } from '../types/work'
import type { WorkMember } from '../types/work'
import { nameInitials } from '../utils/name-initials'
import { MemberRoleSelect } from './member-role-select'

interface MemberRowProps {
  member: WorkMember
  /** Người đang xem từ Quản trị trở lên — mới đổi vai trò / gỡ được. */
  canManage: boolean
  onChangeRole: (employeeId: number, role: number) => void
  onRemove: (memberId: number) => void
}

/**
 * MỘT DÒNG thành viên: avatar · tên + mã · vai trò · nút gỡ.
 *
 * Chủ sở hữu hiện dạng HUY HIỆU có vương miện, và chỉ có thế — không ô chọn vai
 * trò, không nút chuyển quyền. Chủ đầu tư chốt 03/09/2026: quyền sở hữu là thứ
 * chỉ để NHÌN, không đổi được từ giao diện. Backend vẫn giữ endpoint chuyển
 * quyền cho ca dự án mồ côi khi chủ nghỉ việc, gọi tay qua API.
 */
export function MemberRow({ member, canManage, onChangeRole, onRemove }: MemberRowProps) {
  const isOwner = member.role === WORK_ROLE.OWNER
  const name = member.employee_name || `Nhân sự #${member.employee_id}`

  return (
    <li className="flex items-center gap-3 px-3 py-2 transition-colors hover:bg-muted/40">
      <span
        aria-hidden
        className="grid size-8 shrink-0 place-items-center rounded-full border bg-accent text-xs font-medium text-accent-foreground"
      >
        {nameInitials(name)}
      </span>

      <span className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-sm font-medium">{name}</span>
        {member.employee_code && (
          <span className="truncate font-mono text-xs text-muted-foreground">
            {member.employee_code}
          </span>
        )}
      </span>

      {isOwner ? (
        <span className="flex shrink-0 items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-700 dark:text-amber-400">
          <Crown className="size-3.5" />
          Chủ sở hữu
        </span>
      ) : canManage ? (
        <MemberRoleSelect
          value={member.role}
          onChange={(role) => onChangeRole(member.employee_id, role)}
          ariaLabel={`Vai trò của ${name}`}
          className="h-8 w-36 shrink-0"
        />
      ) : (
        <span className="shrink-0 text-xs text-muted-foreground">
          {member.role === WORK_ROLE.ADMIN
            ? 'Quản trị'
            : member.role === WORK_ROLE.MEMBER
              ? 'Thành viên'
              : 'Khách xem'}
        </span>
      )}

      {/*  Khoảng chừa cố định cho nút, kể cả khi nó không hiện: thiếu nó thì dòng
           của chủ sở hữu ngắn hơn các dòng khác và cả cột vai trò so le. */}
      <span className="flex w-9 shrink-0 items-center justify-end">
        {canManage && !isOwner && (
          <IconTooltip label="Gỡ khỏi dự án">
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={`Gỡ ${name} khỏi dự án`}
              onClick={() => onRemove(member.id)}
            >
              <UserMinus className="size-4 text-destructive" />
            </Button>
          </IconTooltip>
        )}
      </span>
    </li>
  )
}
