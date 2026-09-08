import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'
import { LEAVE_STATUS, type LeaveRequest } from '../types/leave'

interface LeaveCalendarEntryProps {
  request: LeaveRequest
  /** `compact` = ô lịch tháng (chật), `full` = hàng tuần. */
  size?: 'compact' | 'full'
}

/**
 * MỘT NGƯỜI NGHỈ trong lịch — dạng chip.
 *
 * ⚠️ Phân biệt **chờ duyệt** với **đã duyệt** bằng MÀU chứ không bằng huy hiệu
 * chữ. Ô lịch tháng cao chừng 90px và chứa được ba dòng; nhét thêm một huy hiệu
 * vào mỗi mục thì hai người nghỉ đã tràn ô. Màu nói đúng điều người xếp việc
 * cần — *chắc chắn nghỉ* hay *có thể nghỉ* — mà không tốn dòng nào.
 *
 * ⚠️ Chip có **nền + viền cùng tông**, không phải một vạch màu bên trái suông.
 * Bản đầu (04/09/2026) chỉ kẻ `border-l-2` trên nền xám: chữ dính sát vạch, và
 * cả cụm đọc ra như một dòng văn bản bị lỗi thụt lề chứ không ra một thẻ bấm
 * được. Nền nhạt khoanh vùng chip lại thì mắt mới tách được người này với người
 * kia trong một ô chật.
 */
export function LeaveCalendarEntry({ request, size = 'compact' }: LeaveCalendarEntryProps) {
  const pending = request.status === LEAVE_STATUS.PENDING
  const name = request.employee_name || `#${request.employee_id}`

  return (
    <Link
      to={appRoutes.hr.leaveRequestDetail(request.id)}
      title={`${name} · ${request.leave_type_name ?? ''} · ${request.status_label ?? ''}`}
      className={cn(
        'flex min-w-0 items-center gap-1.5 rounded border transition-colors',
        pending
          ? 'border-amber-200 bg-amber-50 hover:bg-amber-100 dark:border-amber-900 dark:bg-amber-950/50 dark:hover:bg-amber-950'
          : 'border-emerald-200 bg-emerald-50 hover:bg-emerald-100 dark:border-emerald-900 dark:bg-emerald-950/50 dark:hover:bg-emerald-950',
        size === 'compact' ? 'px-1.5 py-0.5 text-[11px] leading-4' : 'px-2 py-1 text-xs',
      )}
    >
      {/*  Chấm tròn thay cho vạch viền trái: nó nằm TRONG chip nên không bị hiểu
           nhầm là đường kẻ của ô lịch, và vẫn nói được trạng thái ở cỡ 6px. */}
      <span
        aria-hidden="true"
        className={cn(
          'size-1.5 shrink-0 rounded-full',
          pending ? 'bg-amber-500' : 'bg-emerald-500',
        )}
      />
      <span
        className={cn(
          'min-w-0 truncate font-medium',
          pending
            ? 'text-amber-900 dark:text-amber-100'
            : 'text-emerald-900 dark:text-emerald-100',
        )}
      >
        {name}
      </span>
      {size === 'full' && request.leave_type_name && (
        //  Loại nghỉ nhạt hơn tên: tên là thứ người ta tìm, loại nghỉ là chi
        //  tiết đọc sau. `shrink-0` để nó không bị nuốt trước tên khi chật.
        <span
          className={cn(
            'shrink-0 opacity-70',
            pending
              ? 'text-amber-800 dark:text-amber-200'
              : 'text-emerald-800 dark:text-emerald-200',
          )}
        >
          {request.leave_type_name}
        </span>
      )}
    </Link>
  )
}
