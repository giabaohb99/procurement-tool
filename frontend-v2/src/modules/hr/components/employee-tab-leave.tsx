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
    <Card className="gap-4 p-3 sm:p-5">
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

      {/*  ⚠️ Khổ hẹp: hai mốc ngày gom vào MỘT khối có viền, mỗi mốc một hàng
           «nhãn trái — giá trị phải». Bản cũ để lưới một cột nên nhãn và giá
           trị xếp CHỒNG nhau không khung không vạch: bốn dòng chữ trôi nổi giữa
           thẻ, mắt không biết dòng nào ăn với dòng nào, và khoảng hở giữa hai
           cặp trông y như khoảng hở trong một cặp. Từ `sm` giữ lưới hai cột như
           cũ — ở đó bề ngang đủ để hai cặp đứng cạnh nhau đã tự phân nhóm. */}
      <dl className="grid gap-3 text-sm max-md:gap-0 max-md:divide-y max-md:rounded-md max-md:border sm:grid-cols-2">
        <div className="max-md:flex max-md:items-center max-md:justify-between max-md:gap-3 max-md:px-3 max-md:py-2.5">
          <dt className="text-muted-foreground">Ngày vào làm</dt>
          <dd className="font-medium max-md:text-right">
            {formatDate(employee.hire_date) || '— Chưa khai —'}
          </dd>
        </div>
        <div className="max-md:flex max-md:items-center max-md:justify-between max-md:gap-3 max-md:px-3 max-md:py-2.5">
          <dt className="text-muted-foreground">Ngày nghỉ việc</dt>
          <dd className="font-medium max-md:text-right">
            {formatDate(employee.resign_date) || '—'}
          </dd>
        </div>
      </dl>

      <p className="text-sm text-muted-foreground">
        Số phép còn lại được tính từ sổ quỹ, xem bên phân hệ Nghỉ phép.
      </p>

      {/*  Khổ hẹp: hai lối đi CHIA ĐÔI một hàng — chúng cùng hạng với nhau, để
           chúng co theo độ dài chữ thì nút này to nút kia bé mà chẳng vì lý do
           gì. */}
      <div className="flex flex-wrap gap-2">
        {/*  Nút chỉ hiện khi có quyền: bấm vào rồi ăn màn 403 thì tệ hơn không
             thấy nút. Chốt thật vẫn ở backend. */}
        {canSeeBalance && (
          <Button variant="outline" size="sm" className="max-md:flex-1" asChild>
            <Link to={appRoutes.hr.leaveBalances}>
              <CalendarDays />
              Quỹ phép
              <ExternalLink className="size-3" />
            </Link>
          </Button>
        )}
        <Button variant="outline" size="sm" className="max-md:flex-1" asChild>
          <Link to={appRoutes.hr.leaveRequests}>
            Đơn nghỉ phép
            <ExternalLink className="size-3" />
          </Link>
        </Button>
      </div>
    </Card>
  )
}
