import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { formatDate } from '@/shared/utils/format-date'
import { LEAVE_SESSION, LEAVE_SESSION_LABELS, type LeaveRequest } from '../types/leave'

interface LeaveRequestSummaryProps {
  request: LeaveRequest
}

/**
 * BẢN CHỈ XEM của tờ đơn — dùng khi đơn đã gửi duyệt và không sửa được nữa.
 *
 * ⚠️ KHÔNG dựng lại `LeaveRequestForm` với `disabled`. Luật của bộ ERP: ô chỉ
 * xem cấm `<Input disabled>` — `disabled` gỡ luôn khả năng nhận con trỏ nên
 * người dùng không bôi đen, không copy được giá trị, lại còn bị làm mờ 50% nhìn
 * như chữ gợi ý. `ReadOnlyValue` là chữ thật trong khung viền nền mờ.
 */
export function LeaveRequestSummary({ request }: LeaveRequestSummaryProps) {
  //  Buổi chỉ đáng nhắc khi KHÁC «Cả ngày» — thêm "(Cả ngày)" vào mọi dòng là
  //  bốn chữ thừa trên mọi tờ đơn.
  const withSession = (date: string, session: number) => {
    const text = formatDate(date)
    return session === LEAVE_SESSION.FULL
      ? text
      : `${text} (${LEAVE_SESSION_LABELS[session]})`
  }

  return (
    <div className="grid gap-5 md:grid-cols-2">
      <Field label="Người nghỉ" value={request.employee_name || `#${request.employee_id}`} />
      <Field label="Loại nghỉ" value={request.leave_type_name || '—'} />
      <Field label="Từ ngày" value={withSession(request.from_date, request.from_session)} />
      <Field label="Đến ngày" value={withSession(request.to_date, request.to_session)} />
      <Field label="Tổng số ngày" value={`${request.total_days} ngày`} />
      <Field label="Điện thoại liên hệ" value={request.contact_phone || '—'} />

      <div className="md:col-span-2">
        <Field label="Địa chỉ khi nghỉ" value={request.contact_address || '—'} />
      </div>
      <div className="md:col-span-2">
        <Field label="Lý do nghỉ" value={request.reason || '—'} multiline />
      </div>

      {/*  Ý kiến người duyệt KHÔNG lặp lại ở đây: nó đã nằm đúng chỗ của nó trên
           dòng thời gian bên dưới (`LeaveApprovalTimeline`), gắn liền với mốc
           từ chối / trả về / hủy sinh ra nó. */}

      {/*  ⚠️ Khối này LUÔN dựng, kể cả khi không có ai bàn giao.
           Trước 03/09/2026 nó ẩn hẳn khi rỗng, và người duyệt mở tờ đơn ra
           không phân biệt được "người nộp chưa khai ai bàn giao" với "màn hình
           thiếu mục đó" — họ phải đi hỏi. Mà **thiếu người bàn giao chính là lý
           do trả đơn phổ biến nhất**: nó phải nói ra rõ ràng, không phải để
           người đọc suy ra từ một khoảng trống. */}
      <div className="space-y-1.5 md:col-span-2">
        <Label>Bàn giao công việc</Label>
        {request.handovers && request.handovers.length > 0 ? (
          <ul className="divide-y rounded-md border text-sm">
            {request.handovers.map((h) => (
              <li key={h.id} className="flex gap-3 px-3 py-2">
                <span className="shrink-0 font-medium">
                  {h.employee_name || `#${h.employee_id}`}
                </span>
                {/*  `min-w-0` + `break-words`: nội dung bàn giao là chữ tự do,
                     có thể là một chuỗi dài không dấu cách. */}
                <span className="min-w-0 break-words text-muted-foreground">
                  {h.content || '—'}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="rounded-md border border-dashed px-3 py-2.5 text-sm text-muted-foreground">
            Người nộp chưa khai ai nhận bàn giao trong thời gian nghỉ.
          </p>
        )}
      </div>
    </div>
  )
}

function Field({
  label,
  value,
  multiline = false,
}: {
  label: string
  value: string
  multiline?: boolean
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      <ReadOnlyValue multiline={multiline}>{value}</ReadOnlyValue>
    </div>
  )
}
