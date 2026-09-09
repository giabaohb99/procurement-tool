import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { ChartCard } from '@/shared/ui/chart'
import { formatDate } from '@/shared/utils/format-date'
import { LEAVE_GLANCE_DAYS, type LeaveGlance } from '../hooks/use-hr-leave-glance'
import type { LeaveRequest } from '../types/leave'

/** Số dòng bày ra; phần dư chỉ đếm lại thành một câu. */
const MAX_ROWS = 6

interface LeaveGlanceCardProps {
  glance: LeaveGlance
  /** Ô span trên lưới của trang Tổng quan. */
  className?: string
}

/**
 * "Bảy ngày tới ai vắng" — thứ người ta mở trang tổng quan Nhân sự để hỏi.
 *
 * Chỉ liệt kê đơn ĐÃ DUYỆT: đơn còn chờ ký chưa phải là một ngày vắng, đưa vào
 * đây thì người đọc sắp việc theo một lịch chưa chắc xảy ra. Số đơn chờ ký nằm
 * ở thẻ số liệu riêng.
 */
export function LeaveGlanceCard({ glance, className }: LeaveGlanceCardProps) {
  if (!glance.canRead) {
    return (
      <ChartCard
        className={className}
        title="Nghỉ phép sắp tới"
        isEmpty
        emptyLabel="Bạn không có quyền xem đơn nghỉ phép."
      >
        <div />
      </ChartCard>
    )
  }

  const shown = glance.upcoming.slice(0, MAX_ROWS)
  const rest = glance.upcoming.length - shown.length

  return (
    <ChartCard
      className={className}
      title="Nghỉ phép sắp tới"
      description={`Đơn đã duyệt trong ${LEAVE_GLANCE_DAYS} ngày tới, theo phạm vi bạn xem được.`}
      loading={glance.isLoading}
    >
      {/* Câu "rỗng" dựng TRONG nội dung chứ không qua `isEmpty` của `ChartCard`:
          `isEmpty` thay thẳng cả khối con nên dòng chân («Mở lịch nghỉ») mất
          theo — đúng lúc người ta cần nó nhất là lúc tuần này trống và họ muốn
          nhìn xa hơn bảy ngày. Cùng lẽ với thẻ Lịch họp. */}
      <div className="flex flex-1 flex-col">
        {glance.upcoming.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            {LEAVE_GLANCE_DAYS} ngày tới không có ai nghỉ.
          </p>
        ) : (
          <ul className="divide-y">
            {shown.map((request) => (
              <LeaveRow key={request.id} request={request} today={glance.today} />
            ))}
          </ul>
        )}

        {rest > 0 && (
          <p className="pt-2.5 text-xs text-muted-foreground">Và {rest} đơn nữa.</p>
        )}

        {/* `mt-auto` để dòng này luôn nằm đáy thẻ, kể cả khi thẻ bị kéo cao bằng
            biểu đồ nằm cùng hàng. */}
        <Link
          to={appRoutes.hr.leaveCalendar}
          className="mt-auto inline-flex items-center gap-1 pt-3 text-sm font-medium text-primary hover:underline"
        >
          Mở lịch nghỉ
          <ArrowRight className="size-3.5" />
        </Link>
      </div>
    </ChartCard>
  )
}

function LeaveRow({ request, today }: { request: LeaveRequest; today: string }) {
  //  So chuỗi `YYYY-MM-DD` — xem ghi chú ở `use-hr-leave-glance.ts`.
  const isOffToday = request.from_date <= today && request.to_date >= today

  return (
    <li className="py-2.5 first:pt-0">
      <Link
        to={appRoutes.hr.leaveRequestDetail(request.id)}
        className="flex items-center justify-between gap-3 hover:underline"
      >
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-sm font-medium">
            <span className="truncate">{request.employee_name || request.code}</span>
            {isOffToday && (
              <Badge variant="secondary" className="shrink-0 text-[10px]">
                Hôm nay
              </Badge>
            )}
          </p>
          <p className="truncate text-xs text-muted-foreground">
            {request.leave_type_name || 'Nghỉ phép'} · {formatRange(request)}
          </p>
        </div>
        <span className="shrink-0 text-sm tabular-nums text-muted-foreground">
          {request.total_days} ngày
        </span>
      </Link>
    </li>
  )
}

/** Nghỉ trong một ngày thì viết một ngày, đừng viết "10/09 – 10/09". */
function formatRange(request: LeaveRequest): string {
  const from = formatDate(request.from_date)
  if (request.from_date === request.to_date) return from
  return `${from} – ${formatDate(request.to_date)}`
}
