import { ChevronRight, Wallet } from 'lucide-react'

import { formatDate } from '@/shared/utils/format-date'
import { formatEncashDays, isPayoutRejected, type LeaveEncashment } from '../types/leave-encashment'
import { LeaveStatusBadge } from './leave-status-badge'

interface LeaveEncashmentCardProps {
  encashment: LeaveEncashment
  /** Phiếu đang chờ CHÍNH người đăng nhập ký — cùng cờ với cột Trạng thái của bảng. */
  waitingForMe?: boolean
}

/**
 * Một phiếu thanh toán nghỉ phép ở khổ điện thoại (duoc-CR-721) — xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Người được thanh toán lên đầu, số phiếu tụt xuống dòng phụ** — cùng khuôn `LeaveCompRequestCard`:
 * người duyệt nhận ra phiếu bằng người, mã chỉ dùng khi đọc số cho nhau.
 *
 * Loại nghỉ · năm quỹ · lý do · số ngày gom một dòng: bốn vế của cùng câu *"trả mấy ngày phép năm nào, vì
 * sao"*. Trạng thái chi đứng dòng riêng vì nó đọc từ YCTT bên Tài chính, không phải trạng thái của phiếu —
 * và **Kế toán từ chối chi** phải nổi màu như ở bảng (D7a), để phòng Nhân sự biết mà hủy phiếu trả ngày về quỹ.
 *
 * Không in số tiền: phiếu chỉ ghi số ngày, tiền do kế toán nhập ở YCTT (giữ kín lương — xem CR-719).
 */
export function LeaveEncashmentCard({
  encashment: r,
  waitingForMe = false,
}: LeaveEncashmentCardProps) {
  const rejected = isPayoutRejected(r)

  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1 space-y-1.5">
        <div className="flex items-start justify-between gap-2">
          <span className="min-w-0">
            <span className="block truncate font-medium text-foreground">
              {r.employee_name || `#${r.employee_id}`}
            </span>
            <span className="flex flex-wrap items-center gap-x-1 text-xs text-muted-foreground">
              <span className="font-medium text-sky-600 tabular-nums dark:text-sky-400">
                {r.code}
              </span>
              {r.employee_code && (
                <span className="tabular-nums">
                  <span aria-hidden="true">· </span>
                  {r.employee_code}
                </span>
              )}
            </span>
          </span>
          <span className="shrink-0">
            <LeaveStatusBadge status={r.status} label={r.status_label} />
          </span>
        </div>

        {/*  Dấu `·` nằm CÙNG span với vế sau — tách riêng thì lúc xuống dòng nó treo mồ côi ở mép phải. */}
        <div className="flex flex-wrap items-center gap-x-1 gap-y-1 text-sm text-muted-foreground">
          <span>{r.leave_type_name || '—'}</span>
          <span className="tabular-nums">
            <span aria-hidden="true">· </span>
            Năm {r.balance_year}
          </span>
          {r.reason_kind_label && (
            <span>
              <span aria-hidden="true">· </span>
              {r.reason_kind_label}
            </span>
          )}
          <span className="font-medium text-foreground tabular-nums">
            <span aria-hidden="true">· </span>
            {formatEncashDays(r.days)} ngày
          </span>
        </div>

        {waitingForMe && (
          <p className="text-xs font-medium text-sky-700 dark:text-sky-300">Cần bạn duyệt</p>
        )}

        {(rejected || r.payment_status) && (
          <p className="flex items-center gap-1 text-xs">
            <Wallet className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
            {rejected ? (
              <span className="font-medium text-amber-700 dark:text-amber-300">
                Kế toán từ chối chi
              </span>
            ) : (
              <span className="text-muted-foreground">{r.payment_status_label}</span>
            )}
          </p>
        )}

        {r.note && (
          <p className="line-clamp-2 text-sm break-words text-muted-foreground">{r.note}</p>
        )}

        <p className="text-xs text-muted-foreground tabular-nums">
          Ngày tạo {formatDate(r.created_at)}
        </p>
      </div>

      {/*  Mũi tên nói thẻ bấm được — màn cảm ứng không có con trỏ đổi hình như khi rê dòng bảng. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </div>
  )
}
