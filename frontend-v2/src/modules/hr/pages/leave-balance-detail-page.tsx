import { ArrowLeft } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { LeaveBalanceAdjustCard } from '../components/leave-balance-adjust-card'
import { LeaveBalanceBreakdownCard } from '../components/leave-balance-breakdown-card'
import { LeaveBalanceRequestsCard } from '../components/leave-balance-requests-card'
import { useLeaveBalance } from '../hooks/use-leave'

/**
 * CHI TIẾT MỘT DÒNG QUỸ PHÉP — `/hr/leave-balances/:id`.
 *
 * ⚠️ Là một TRANG chứ không phải hộp thoại (đổi 03/09/2026). Bản đầu mở popup
 * «Điều chỉnh quỹ phép» ngay từ dòng, và popup thì buộc phải gói gọn: mọi thứ
 * giải thích cho con số đang sửa — quỹ cấu thành từ đâu, người này đã nghỉ
 * những hôm nào — đều nằm ngoài nó. Người dùng đóng popup ra xem rồi mở lại, và
 * lúc mở lại thì phải nhớ mình vừa đọc gì.
 *
 * Ba thẻ theo đúng thứ tự người ta hỏi: **quỹ đang thế nào** → **vì sao thế**
 * (những đơn đã nghỉ) → **sửa lại**. Thẻ sửa đứng cuối là cố ý: nó là thao tác
 * nhạy cảm nhất của cả phân hệ (tặng ngày phép cho người khác), nên phải đọc
 * xong hai thẻ trên rồi mới tới.
 */
export function LeaveBalanceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const balanceId = Number(id) || 0
  const navigate = useNavigate()
  const { can } = usePermission()

  const { data: balance, isLoading } = useLeaveBalance(balanceId)

  if (isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Đang tải dòng quỹ…</p>
      </PageContainer>
    )
  }

  if (!balance) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">
          Không tìm thấy dòng quỹ phép này, hoặc nó nằm ngoài phạm vi dữ liệu của bạn.
        </p>
      </PageContainer>
    )
  }

  const employeeName = balance.employee_name || `#${balance.employee_id}`

  return (
    <PageContainer>
      <PageHeader
        leading={
          <Button
            variant="outline"
            size="icon"
            title="Về danh sách quỹ phép"
            aria-label="Về danh sách quỹ phép"
            onClick={() => navigate(appRoutes.hr.leaveBalances)}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
        title={employeeName}
        description={`${balance.leave_type_name || `#${balance.leave_type_id}`} · năm ${balance.year}`}
      />

      <div className="space-y-4">
        <LeaveBalanceBreakdownCard balance={balance} />
        <LeaveBalanceRequestsCard balance={balance} />
        {/*  Chỉ dựng thẻ sửa khi có quyền: hiện form rồi chặn lúc bấm Lưu là
             bắt người ta gõ xong mới biết mình không được phép. */}
        {can('leave_balance', 'write') && <LeaveBalanceAdjustCard balance={balance} />}
      </div>
    </PageContainer>
  )
}
