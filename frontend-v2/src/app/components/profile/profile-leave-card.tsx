import { CalendarDays, ExternalLink, TriangleAlert } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { useLeaveBalances } from '@/modules/hr/hooks/use-leave'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { FormCard } from '@/shared/ui/form-card'
import { Skeleton } from '@/shared/ui/skeleton'

interface ProfileLeaveCardProps {
  employeeId: number
  /** Có ngày vào làm chưa — mốc tính thâm niên, tức phần ngày phép cộng thêm. */
  hasHireDate: boolean
}

/** Số ngày bỏ đuôi `.0` nhưng giữ `.5` — quỹ phép đếm theo nửa ngày. */
function formatDays(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

/**
 * QUỸ PHÉP của chính mình ở Trang cá nhân — *«còn bao nhiêu ngày phép»*.
 *
 * ⚠️ **Đọc cửa danh sách có sẵn, KHÔNG mở cửa `/me` riêng như hồ sơ nhân sự.**
 * Hai ca nhìn giống nhau nhưng khác gốc:
 *
 * - `employee.read` là khóa xem hồ sơ NGƯỜI KHÁC, và **không có đường nào** đọc
 *   hồ sơ của chính mình mà không cầm khóa đó — một lỗ hổng thiết kế, nên
 *   duoc-CR-378 phải mở cửa `/api/employees/me`.
 * - Quỹ phép thì **đã có sẵn đường**: `leave_balance.read` cộng phạm vi `own`.
 *   Ghi chú của chính cửa danh sách nói thẳng *«Quỹ của tôi» khi phạm vi = own*.
 *   Đục thêm một cửa `/me` ở đây là phá cái cơ chế đang chạy đúng, và bỏ qua
 *   quyết định của bộ phận Nhân sự về việc ai được xem quỹ.
 *
 * ⚠️ Vì vậy **phải tự tắt khi thiếu khóa** (`enabled`), đừng cứ mount là gọi:
 * quỹ phép là phân hệ khác, người không được cấp `leave_balance.read` sẽ ăn một
 * toast 403 ngay lúc mở trang cá nhân — chẳng liên quan gì tới việc họ đang làm.
 *
 * ⚠️ **Không tự cộng trừ lại con số.** `remaining_days` do
 * `balance_service.remaining()` tính; đó là nơi DUY NHẤT tính ra nó, và cả công
 * ty nhìn vào con số ấy để xin nghỉ. Dựng lại công thức ở đây là đẻ ra nguồn thứ
 * hai — cùng lý do mà tab «Quỹ phép» của màn hồ sơ nhân sự cố ý chỉ dẫn đường
 * chứ không chép bảng.
 */
export function ProfileLeaveCard({ employeeId, hasHireDate }: ProfileLeaveCardProps) {
  const { can } = usePermission()
  const canRead = can('leave_balance', 'read')
  const year = new Date().getFullYear()

  const { data, isPending } = useLeaveBalances(
    //  `page_size` rộng tay: mỗi người chỉ vài dòng (một dòng một loại nghỉ),
    //  phân trang ở đây chỉ tổ giấu mất một loại.
    { employee_id: employeeId, year, page_size: 50 },
    { enabled: canRead && employeeId > 0 },
  )

  //  Thiếu khóa thì KHÔNG dựng thẻ: bày một thẻ rỗng kèm câu «bạn không có
  //  quyền» chỉ làm người dùng đi hỏi một thứ họ không cần.
  if (!canRead) return null

  const rows = data?.items ?? []

  return (
    <FormCard
      title={`Quỹ phép ${year}`}
      icon={CalendarDays}
      iconClassName="text-muted-foreground"
      actions={
        <Button variant="outline" size="sm" asChild>
          <Link to={appRoutes.hr.leaveRequests}>
            <ExternalLink className="size-4" />
            Đơn nghỉ phép
          </Link>
        </Button>
      }
    >
      {/*  ⚠️ Cảnh báo THIẾU NGÀY VÀO LÀM phải có ở đây, giống tab «Quỹ phép» của
           màn hồ sơ nhân sự: không có mốc đó thì thâm niên tính bằng 0 năm và
           người này **mất phần ngày phép cộng thêm** — mà không màn nào khác
           báo. Người xem hồ sơ của chính mình là người có động cơ đi đòi sửa
           nhất, nên chỗ này đáng nói hơn cả. */}
      {!hasHireDate && (
        <div className="mb-3 flex items-start gap-2 rounded-md border border-dashed p-3 text-sm">
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-destructive" />
          <span>
            Hồ sơ <strong>chưa có Ngày vào làm</strong> nên chưa tính được thâm niên, phần ngày
            phép cộng thêm cũng chưa áp dụng. Liên hệ bộ phận Nhân sự để bổ sung.
          </span>
        </div>
      )}

      {isPending ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : rows.length === 0 ? (
        <p className="py-2 text-sm text-muted-foreground">
          Chưa có dòng quỹ phép nào cho năm {year}.
        </p>
      ) : (
        <div className="divide-y rounded-md border">
          {rows.map((row) => (
            <div
              key={row.id}
              className="flex items-center justify-between gap-3 px-3 py-2.5 text-sm"
            >
              <span className="min-w-0 flex-1 truncate">{row.leave_type_name || '—'}</span>

              {/*  Con số CÒN LẠI to và đậm, tổng để mờ bên cạnh: câu hỏi người ta
                   mở thẻ này ra để hỏi là «còn mấy ngày», không phải «được cấp
                   mấy ngày». */}
              <span className="shrink-0 tabular-nums">
                <span className="font-semibold text-navy dark:text-foreground">
                  {formatDays(row.remaining_days)}
                </span>
                <span className="text-muted-foreground"> / {formatDays(row.total_days)} ngày</span>
              </span>
            </div>
          ))}
        </div>
      )}

      {/*  ⚠️ Nói rõ phần GIỮ CHỖ. `pending_days` đã bị trừ khỏi `remaining_days`
           ngay lúc gửi duyệt (chốt của phân hệ Nghỉ phép), nên người vừa nộp đơn
           thấy số tụt xuống mà chưa ai duyệt — không giải thích thì họ tưởng hệ
           thống trừ nhầm. */}
      {rows.some((row) => row.pending_days > 0) && (
        <p className="mt-3 text-xs text-muted-foreground">
          Số còn lại đã trừ phần đang giữ chỗ cho đơn <strong>chờ duyệt</strong>.
        </p>
      )}
    </FormCard>
  )
}
