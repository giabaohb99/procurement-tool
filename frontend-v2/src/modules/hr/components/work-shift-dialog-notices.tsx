import { ExternalLink, Lock } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import type { WorkRosterLeave } from '../types/work-roster'

interface WorkShiftDialogNoticesProps {
  /** Lý do ô chỉ xem (chính mình · ngày đã qua · có đơn nghỉ…); `null` = sửa được. */
  lockHint: string | null
  leave: WorkRosterLeave | null | undefined
}

/**
 * Dòng lý do ngay trên chân hộp xếp ca: chữ mờ nhỏ kèm ổ khóa (KHÔNG khung nét đứt — trông như báo lỗi, đại ca chê),
 * và đơn nghỉ đang phủ ngày đó kèm link sang đơn.
 */
export function WorkShiftDialogNotices({ lockHint, leave }: WorkShiftDialogNoticesProps) {
  if (!lockHint && !leave) return null
  return (
    <div className="space-y-1 text-xs text-muted-foreground">
      {lockHint && (
        <p className="flex items-start gap-1.5">
          <Lock aria-hidden className="mt-px size-3.5 shrink-0" />
          {lockHint}
        </p>
      )}
      {leave && (
        <p>
          Đơn nghỉ <span className="font-medium text-foreground">{leave.code}</span> ({leave.leave_type_name},{' '}
          {leave.is_approved ? 'đã duyệt' : 'chờ duyệt'}) —{' '}
          <Link
            to={appRoutes.hr.leaveRequestDetail(leave.request_id)}
            className="inline-flex items-center gap-1 text-primary underline-offset-2 hover:underline"
          >
            xem đơn
            <ExternalLink aria-hidden className="size-3" />
          </Link>
        </p>
      )}
    </div>
  )
}
