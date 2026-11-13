import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import type { BackOrigin } from '@/shared/hooks/use-back-target'
import { Badge } from '@/shared/ui/badge'
import type { ConcurrentMember } from '../types/concurrent-member'
import { needsStatusBadge } from '../utils/concurrent-member-display'

interface ConcurrentMemberNameProps {
  member: ConcurrentMember
  backState: BackOrigin
  /** Tắt khi bảng đã có cột Trạng thái riêng (trang công ty) — khỏi nói hai lần. */
  showStatus?: boolean
}

/**
 * Họ tên người kiêm nhiệm + huy hiệu **Kiêm nhiệm** (và Sắp tới / Đã hết nếu dòng chưa / không còn hiệu lực) — dùng
 * chung cho bảng ở trang phòng ban và trang công ty. Tên chỉ là liên kết khi `can_open`: dòng tắt công tắc "Tính vào
 * phạm vi quyền" thì người xem thấy tên nhưng không mở được hồ sơ.
 */
export function ConcurrentMemberName({ member, backState, showStatus = true }: ConcurrentMemberNameProps) {
  return (
    <span className="flex min-w-0 items-center gap-2">
      {member.can_open ? (
        <Link
          to={appRoutes.hr.employeeDetail(member.employee_id)}
          state={backState}
          className="truncate font-medium text-primary underline-offset-2 hover:underline"
          onClick={(event) => event.stopPropagation()}
        >
          {member.full_name}
        </Link>
      ) : (
        <span className="truncate" title="Bạn chỉ xem được dòng kiêm nhiệm này, không mở được hồ sơ">
          {member.full_name}
        </span>
      )}
      <Badge variant="outline" className="shrink-0">
        Kiêm nhiệm
      </Badge>
      {showStatus && needsStatusBadge(member) && (
        <Badge variant="secondary" className="shrink-0">
          {member.status_label}
        </Badge>
      )}
    </span>
  )
}
