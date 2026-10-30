import type { EmployeeChangeRequest } from '../types/employee-change-request'
import { CHANGE_REQUEST_STATUS } from '../utils/employee-change-request-status'
import { Card } from '@/shared/ui/card'
import { formatDateTime } from '@/shared/utils/format-date'

/**
 * Khối "gửi lúc / xử lý lúc / ghi chú / lý do từ chối" của màn duyệt một đề nghị sửa hồ sơ
 * (duoc-CR-676). Ghi chú luôn có dòng, kể cả khi trống — người duyệt cần biết nhân viên KHÔNG ghi
 * gì, chứ không phải màn thiếu mục.
 */
export function ChangeRequestSummaryCard({ request }: { request: EmployeeChangeRequest }) {
  return (
    <Card className="mb-5 gap-2 p-5 text-sm">
      <div>
        <span className="text-muted-foreground">Gửi lúc: </span>
        {formatDateTime(request.created_at)}
      </div>
      {request.decided_at && (
        <div>
          <span className="text-muted-foreground">Xử lý lúc: </span>
          {formatDateTime(request.decided_at)}
          {request.decided_by_name && ` — ${request.decided_by_name}`}
        </div>
      )}
      <div>
        <span className="text-muted-foreground">Ghi chú của nhân viên: </span>
        {request.note || <span className="text-muted-foreground">(không có)</span>}
      </div>
      {request.status === CHANGE_REQUEST_STATUS.REJECTED && request.reject_reason && (
        <div>
          <span className="font-medium text-destructive">Lý do từ chối: </span>
          {request.reject_reason}
        </div>
      )}
    </Card>
  )
}
