import { CalendarDays, ExternalLink, TriangleAlert } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { SectionHeading } from '@/shared/ui/section-heading'
import { formatDate } from '@/shared/utils/format-date'
import type { EmployeeDetail } from '../types/employee'

interface EmployeeTabLeaveProps {
  employee: EmployeeDetail
}

/**
 * Tab «Quỹ phép» — CỐ Ý chỉ là một lối đi sang phân hệ Nghỉ phép, không dựng
 * lại bảng quỹ ở đây.
 *
 * Số phép còn lại KHÔNG lưu thành cột: `balance_service.remaining()` là nơi duy
 * nhất tính ra nó. Chép một bản hiển thị sang màn hồ sơ là đẻ ra nguồn thứ hai
 * cho một con số mà cả công ty nhìn vào để xin nghỉ.
 *
 * Việc DUY NHẤT tab này làm thêm: cảnh báo hồ sơ thiếu **ngày vào làm** — mốc
 * thâm niên. Thiếu nó thì người này bị tính 0 năm và mất phần phép cộng thêm,
 * mà không màn nào khác báo.
 */
export function EmployeeTabLeave({ employee }: EmployeeTabLeaveProps) {
  const { can } = usePermission()
  const canSeeBalance = can('leave_balance', 'read')

  return (
    <Card className="gap-4 p-5">
      <SectionHeading>Quỹ phép</SectionHeading>

      {!employee.hire_date && (
        <div className="flex items-start gap-2 rounded-md border border-dashed p-3 text-sm">
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-destructive" />
          <span>
            Hồ sơ <strong>chưa có Ngày vào làm</strong> nên chưa tính được thâm niên, và
            phần ngày phép cộng thêm cũng chưa áp dụng. Nhập ở tab <strong>Chung</strong>.
          </span>
        </div>
      )}

      <dl className="grid gap-3 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-muted-foreground">Ngày vào làm</dt>
          <dd className="font-medium">{formatDate(employee.hire_date) || '— Chưa khai —'}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Ngày nghỉ việc</dt>
          <dd className="font-medium">{formatDate(employee.resign_date) || '—'}</dd>
        </div>
      </dl>

      <p className="text-sm text-muted-foreground">
        Số phép còn lại được tính từ sổ quỹ, xem bên phân hệ Nghỉ phép.
      </p>

      <div className="flex flex-wrap gap-2">
        {/*  Nút chỉ hiện khi có quyền: bấm vào rồi ăn màn 403 thì tệ hơn không
             thấy nút. Chốt thật vẫn ở backend. */}
        {canSeeBalance && (
          <Button variant="outline" size="sm" asChild>
            <Link to={appRoutes.hr.leaveBalances}>
              <CalendarDays />
              Quỹ phép
              <ExternalLink className="size-3" />
            </Link>
          </Button>
        )}
        <Button variant="outline" size="sm" asChild>
          <Link to={appRoutes.hr.leaveRequests}>
            Đơn nghỉ phép
            <ExternalLink className="size-3" />
          </Link>
        </Button>
      </div>
    </Card>
  )
}
