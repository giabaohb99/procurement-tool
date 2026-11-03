import { Card, CardContent } from '@/shared/ui/card'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import type { LeaveCompRequest } from '../types/leave-comp'
import { formatCompDays } from '../utils/format-comp-days'

interface LeaveCompRequestSummaryProps {
  request: LeaveCompRequest
}

/**
 * BẢN CHỈ XEM của phiếu nghỉ bù (đã gửi duyệt, không sửa được nữa).
 * Cùng ngôn ngữ "nhãn – giá trị" với `LeaveRequestSummary`; không dựng form với `disabled`.
 */
export function LeaveCompRequestSummary({ request }: LeaveCompRequestSummaryProps) {
  return (
    <Card className="py-4 sm:py-6">
      <CardContent className="px-3 sm:px-6">
        <dl className="divide-y overflow-hidden rounded-md border">
          <Row label="Người nghỉ" value={request.employee_name || `#${request.employee_id}`} />
          <Row label="Phòng ban" value={request.department_name} />
          <Row label="Ngày đã đi làm" value={formatDate(request.work_date)} />
          <Row label="Số ngày nghỉ bù" value={`${formatCompDays(request.days)} ngày`} />
          <Row label="Lý do đi làm" value={request.reason} multiline />
          {request.decided_at && (
            <Row label="Chốt lúc" value={formatDateTime(request.decided_at)} />
          )}
          {request.decision_note?.trim() && (
            <Row label="Ghi chú của người chốt" value={request.decision_note} multiline />
          )}
        </dl>
      </CardContent>
    </Card>
  )
}

function Row({ label, value, multiline = false }: { label: string; value?: string; multiline?: boolean }) {
  const text = (value ?? '').trim()
  return (
    <div className="grid gap-x-4 px-3 py-2 sm:grid-cols-[11rem_minmax(0,1fr)] sm:items-baseline">
      <dt className="text-xs text-muted-foreground sm:text-sm">{label}</dt>
      <dd className={multiline ? 'text-sm font-medium break-words whitespace-pre-wrap' : 'text-sm font-medium break-words'}>
        {text || <span className="text-muted-foreground">—</span>}
      </dd>
    </div>
  )
}
