import { Crown, Send, UserMinus } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { formatDate } from '@/shared/utils/format-date'
import { WORK_ROLE } from '../types/work'
import type { WorkMember } from '../types/work'
import { nameInitials } from '../utils/name-initials'
import { MemberRoleSelect } from './member-role-select'
import { PersonAvatar } from './person-avatar'

interface MemberRowProps {
  member: WorkMember
  /** Người đang xem từ Quản trị trở lên — mới đổi vai trò / gỡ được. */
  canManage: boolean
  /** Gỡ khỏi cái gì — "dự án" / "nhóm dự án" (hai hộp Quản lý dùng chung dòng này). */
  removeTarget: string
  onChangeRole: (employeeId: number, role: number) => void
  onRemove: (memberId: number) => void
  onReinvite: (memberId: number) => void
}

/** Bấm Mời lại xong thì khóa nút chừng này — bấm liên tục là dội chuông vào người được mời. */
const REINVITE_COOLDOWN_MS = 30_000

/**
 * MỘT DÒNG thành viên: avatar · tên + mã · vai trò · nút gỡ.
 *
 * Chủ sở hữu hiện dạng HUY HIỆU có vương miện, và chỉ có thế — không ô chọn vai
 * trò, không nút chuyển quyền. Chủ đầu tư chốt 03/09/2026: quyền sở hữu là thứ
 * chỉ để NHÌN, không đổi được từ giao diện. Backend vẫn giữ endpoint chuyển
 * quyền cho ca dự án mồ côi khi chủ nghỉ việc, gọi tay qua API.
 */
export function MemberRow({
  member,
  canManage,
  removeTarget,
  onChangeRole,
  onRemove,
  onReinvite,
}: MemberRowProps) {
  const isOwner = member.role === WORK_ROLE.OWNER
  const name = member.employee_name || `Nhân sự #${member.employee_id}`

  //  Khóa bằng ref NGAY trong lượt bấm (state chỉ đổi ở lượt render sau — bấm đúp vẫn lọt), state chỉ để vẽ nút mờ.
  const reinviteLock = useRef(false)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [cooling, setCooling] = useState(false)
  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current)
  }, [])
  function reinvite() {
    if (reinviteLock.current) return
    reinviteLock.current = true
    setCooling(true)
    onReinvite(member.id)
    timer.current = setTimeout(() => {
      reinviteLock.current = false
      setCooling(false)
    }, REINVITE_COOLDOWN_MS)
  }

  return (
    <li className="flex items-center gap-3 px-3 py-2 transition-colors hover:bg-muted/40">
      <PersonAvatar
        name={name}
        avatar={member.avatar}
        initials={nameInitials(name)}
        className="size-8 text-xs"
      />

      <span className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-sm font-medium">{name}</span>
        <span className="flex min-w-0 items-center gap-1.5 text-xs text-muted-foreground">
          {member.employee_code && <span className="truncate font-mono">{member.employee_code}</span>}
          {/*  duoc-CR-783: "Đã mời <ngày>" — anh Được: "mời thì phải để là đã mời". Chủ sở hữu là người tạo, không ai mời. */}
          {!isOwner && member.invited_at && (
            <span className="shrink-0 rounded bg-muted px-1.5 py-px">Đã mời {formatDate(member.invited_at)}</span>
          )}
        </span>
      </span>

      {isOwner ? (
        //  Khung rộng ĐÚNG bằng ô chọn vai trò (w-36) và căn trái như chữ trong ô: huy hiệu để trần thì hẹp hơn nên trôi
        //  ra giữa dòng, lệch khỏi cột vai trò của các dòng dưới.
        <span className="flex w-36 shrink-0">
          <span className="flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-700 dark:text-amber-400">
            <Crown className="size-3.5" />
            Chủ sở hữu
          </span>
        </span>
      ) : canManage ? (
        <MemberRoleSelect
          value={member.role}
          onChange={(role) => onChangeRole(member.employee_id, role)}
          ariaLabel={`Vai trò của ${name}`}
          className="h-8 w-36 shrink-0"
        />
      ) : (
        <span className="w-36 shrink-0 text-xs text-muted-foreground">
          {member.role === WORK_ROLE.ADMIN
            ? 'Quản trị'
            : member.role === WORK_ROLE.MEMBER
              ? 'Thành viên'
              : 'Khách xem'}
        </span>
      )}

      {/*  Khoảng chừa cố định cho hai nút, kể cả khi chúng không hiện: thiếu nó thì dòng
           của chủ sở hữu ngắn hơn các dòng khác và cả cột vai trò so le. */}
      <span className="flex w-[4.5rem] shrink-0 items-center justify-end gap-0.5">
        {canManage && !isOwner && (
          <IconTooltip label={cooling ? 'Vừa gửi lại lời mời' : 'Mời lại (gửi lại thông báo)'}>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={`Mời lại ${name}`}
              disabled={cooling}
              onClick={reinvite}
            >
              <Send className="size-4 text-muted-foreground" />
            </Button>
          </IconTooltip>
        )}
        {canManage && !isOwner && (
          <IconTooltip label={`Gỡ khỏi ${removeTarget}`}>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={`Gỡ ${name} khỏi ${removeTarget}`}
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
