import { CalendarDays, ChevronRight, MessageSquareWarning } from 'lucide-react'

import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import type { LeaveRequest } from '../types/leave'
import { decisionNoteLabelOf, decisionNoteOf } from '../utils/leave-decision-note'
import { leaveLinesText, leaveTypeLabel } from '../utils/leave-type-label'
import { LeaveStatusBadge } from './leave-status-badge'

interface LeaveRequestCardProps {
  request: LeaveRequest
  /**
   * Bày huy hiệu trạng thái không. Tab «Cần tôi duyệt» tắt: mọi đơn ở đó đều là
   * «Chờ duyệt», một huy hiệu lặp lại y hệt trên từng thẻ chỉ ăn chỗ của dòng
   * chữ đứng cạnh nó — đúng lý do bảng cũng không có cột Trạng thái ở tab đó.
   */
  showStatus?: boolean
  /**
   * Bày tên người nghỉ không. Tắt ở màn CHI TIẾT MỘT DÒNG QUỸ PHÉP: cả danh
   * sách ở đó là đơn của đúng một người, mà tên người ấy đã nằm ngay trên tiêu
   * đề trang — lặp lại trên từng thẻ chỉ ăn mất dòng đầu. Bảng ở màn đó cũng
   * không có cột Nhân sự, cùng một lý do.
   */
  showEmployee?: boolean
  /** Hạn xử lý việc duyệt — chỉ tab «Cần tôi duyệt» có. */
  dueAt?: string | null
}

/**
 * Một tờ đơn nghỉ phép ở chế độ MÀN HẸP — xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Thứ tự trong thẻ không phải thứ tự cột của bảng.** Bảng xếp «Số đơn»
 * trước vì cột đầu là cột định danh và nó được ghim; trên thẻ thì mã đơn là thứ
 * ÍT dùng nhất — người duyệt nhận ra tờ đơn bằng TÊN NGƯỜI và KHOẢNG NGÀY, mã
 * chỉ dùng khi đọc số cho nhau qua điện thoại. Nên tên lên đầu, mã tụt xuống
 * dòng chân cùng cỡ chữ nhỏ.
 *
 * ⚠️ **Lý do nghỉ chặn ở hai dòng (`line-clamp-2`).** Ô `reason` không giới hạn
 * độ dài ở tầng nhập, và một tờ đơn có lý do 40 dòng sẽ đẩy chín tờ còn lại ra
 * khỏi màn hình — người duyệt cuộn cả trang chỉ để đi qua MỘT đơn. Bản đủ nằm ở
 * chi tiết, mà thẻ nào cũng bấm vào chi tiết được.
 *
 * ⚠️ **Không tooltip trong thẻ.** Trên thiết bị cảm ứng không có nhịp «rê chuột»
 * nên tooltip hoặc không mở được, hoặc mở ra rồi che mất chính dòng vừa bấm.
 * Lý do bị từ chối / trả về vì thế hiện thẳng thành chữ (bảng thì giấu trong
 * tooltip vì ô cao 35px không chứa nổi).
 */
export function LeaveRequestCard({
  request,
  showStatus = true,
  showEmployee = true,
  dueAt,
}: LeaveRequestCardProps) {
  const note = decisionNoteOf(request)
  const linesText = leaveLinesText(request)

  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1 space-y-1.5">
        {/*  Hàng đầu: thứ ĐỊNH DANH tờ đơn trong ngữ cảnh này + trạng thái.
             Bình thường là tên người; danh sách một-người thì tên vô nghĩa nên
             mã đơn lên thay (và dòng chân bỏ mã đi, không in hai lần).
             `min-w-0` + `truncate` trên khối bên trái — thiếu nó thì tên dài đẩy
             huy hiệu tràn ra ngoài mép thẻ. */}
        <div className="flex items-start justify-between gap-2">
          <span className="min-w-0 truncate font-medium text-foreground tabular-nums">
            {showEmployee ? request.employee_name || `#${request.employee_id}` : request.code}
          </span>
          {showStatus && (
            <span className="shrink-0">
              <LeaveStatusBadge status={request.status} label={request.status_label} />
            </span>
          )}
        </div>

        {/*  Khoảng ngày + số ngày đứng chung một dòng: đây là câu trả lời cho
             «nghỉ khi nào, mấy ngày» — hai vế của cùng một câu hỏi, tách hai
             dòng thì mắt phải ghép lại.

             ⚠️ Dấu `·` phải nằm CÙNG span với vế đứng sau nó. Tách thành phần tử
             flex riêng thì lúc xuống dòng nó ở lại cuối dòng trên, thành một dấu
             chấm giữa mồ côi treo ở mép phải. */}
        <div className="flex flex-wrap items-center gap-x-1.5 gap-y-1 text-sm text-muted-foreground">
          <CalendarDays className="size-3.5 shrink-0" aria-hidden="true" />
          <span className="tabular-nums">
            {formatDate(request.from_date)} – {formatDate(request.to_date)}
          </span>
          <span className="font-medium text-foreground tabular-nums">
            <span aria-hidden="true">· </span>
            {request.total_days} ngày
          </span>
        </div>

        {/*  ⚠️ Loại nghỉ đứng RIÊNG và có KHUNG, không nối đuôi dòng ngày như ở
             bảng. Trên thẻ nó nằm ngay trên lý do nghỉ — cả hai đều là chữ tự do
             cỡ như nhau, nên để trần thì «Nghỉ không lương 1 ngày» và «Nghỉ tập
             thể…» đọc thành hai câu cùng loại và người xem không biết câu nào là
             loại nghỉ, câu nào là lý do. Khung mảnh tách hẳn hai vai.

             Đơn nhiều loại nói ĐỦ bản kê chứ không rút thành «+1» như ô bảng:
             thẻ có chỗ để xuống dòng, mà «+1» thì người đọc không biết cái +1 đó
             là loại gì. */}
        <div className="flex flex-wrap gap-1">
          <span className="rounded border px-1.5 py-0.5 text-xs break-words text-foreground">
            {linesText || leaveTypeLabel(request)}
          </span>
        </div>

        {request.reason && (
          <p className="line-clamp-2 text-sm break-words text-muted-foreground">
            {request.reason}
          </p>
        )}

        {note && (
          <p className="flex items-start gap-1 text-xs break-words text-muted-foreground">
            <MessageSquareWarning className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
            <span>
              <span className="font-medium">{decisionNoteLabelOf(request.status)}:</span> {note}
            </span>
          </p>
        )}

        {(showEmployee || dueAt) && (
          <div className="flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground">
            {showEmployee && <span className="tabular-nums">{request.code}</span>}
            {showEmployee && dueAt && <span aria-hidden="true">·</span>}
            {dueAt && <span className="tabular-nums">Hạn xử lý {formatDateTime(dueAt)}</span>}
          </div>
        )}
      </div>

      {/*  Mũi tên nói THẺ NÀY BẤM ĐƯỢC. Trên bảng, con trỏ đổi hình khi rê qua
           dòng đã nói điều đó; màn cảm ứng không có con trỏ nên phải nói bằng
           hình. */}
      <ChevronRight className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
    </div>
  )
}
