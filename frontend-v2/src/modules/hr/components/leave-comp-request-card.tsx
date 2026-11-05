import { CalendarDays, ChevronRight, MessageSquareWarning } from 'lucide-react'

import { formatDate } from '@/shared/utils/format-date'
import type { LeaveCompRequest } from '../types/leave-comp'
import { formatCompDays } from '../utils/format-comp-days'
import { LeaveStatusBadge } from './leave-status-badge'

interface LeaveCompRequestCardProps {
  request: LeaveCompRequest
  /** Phiếu đang nằm trong hàng đợi duyệt của người đăng nhập — cùng cờ với cột Trạng thái của bảng. */
  waitingForMe?: boolean
}

/**
 * Một phiếu xin nghỉ bù ở khổ điện thoại (duoc-CR-721) — xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Tên người nghỉ lên đầu, số phiếu tụt xuống dòng phụ** — cùng lý do với `LeaveRequestCard`: người
 * duyệt nhận ra phiếu bằng người và ngày đi làm, mã chỉ dùng khi đọc số cho nhau. Bảng xếp Số phiếu
 * trước vì đó là cột ghim.
 *
 * Ngày đi làm + số ngày bù đứng chung một dòng: hai vế của cùng câu hỏi *"làm hôm nào, được bù mấy ngày"*.
 * Lý do (bảng để ẩn mặc định) hiện ở thẻ nhưng chặn hai dòng: ô nhập không giới hạn độ dài, bản đủ
 * nằm ở chi tiết. Cả thẻ là vùng bấm vào chi tiết nên trong thẻ không có nút nào.
 */
export function LeaveCompRequestCard({ request, waitingForMe = false }: LeaveCompRequestCardProps) {
  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1 space-y-1.5">
        <div className="flex items-start justify-between gap-2">
          <span className="min-w-0">
            <span className="block truncate font-medium text-foreground">
              {request.employee_name || `#${request.employee_id}`}
            </span>
            <span className="flex flex-wrap items-center gap-x-1 text-xs text-muted-foreground">
              <span className="font-medium text-sky-600 tabular-nums dark:text-sky-400">{request.code}</span>
              {request.employee_code && (
                <span className="tabular-nums">
                  <span aria-hidden="true">· </span>
                  {request.employee_code}
                </span>
              )}
            </span>
          </span>
          <span className="shrink-0">
            <LeaveStatusBadge status={request.status} label={request.status_label} />
          </span>
        </div>

        {/*  Dấu `·` nằm CÙNG span với vế sau — tách riêng thì lúc xuống dòng nó treo mồ côi ở mép phải. */}
        <div className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-sm text-muted-foreground">
          <CalendarDays className="size-3.5 shrink-0" aria-hidden="true" />
          <span className="tabular-nums">Đi làm {formatDate(request.work_date)}</span>
          <span className="font-medium text-foreground tabular-nums">
            <span aria-hidden="true">· </span>
            {formatCompDays(request.days)} ngày
          </span>
        </div>

        {waitingForMe && (
          <p className="text-xs font-medium text-sky-700 dark:text-sky-300">Cần bạn duyệt</p>
        )}

        {request.reason && (
          <p className="line-clamp-2 text-sm break-words text-muted-foreground">{request.reason}</p>
        )}

        {request.decision_note && (
          <p className="flex items-start gap-1 text-xs break-words text-muted-foreground">
            <MessageSquareWarning className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
            <span>{request.decision_note}</span>
          </p>
        )}

        <p className="text-xs text-muted-foreground tabular-nums">Ngày tạo {formatDate(request.created_at)}</p>
      </div>

      {/*  Mũi tên nói thẻ bấm được — màn cảm ứng không có con trỏ đổi hình như khi rê dòng bảng. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </div>
  )
}
