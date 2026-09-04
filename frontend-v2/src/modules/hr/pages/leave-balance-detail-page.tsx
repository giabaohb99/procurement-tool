import { ArrowLeft, Save } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { LeaveBalanceAdjustCard } from '../components/leave-balance-adjust-card'
import { LeaveBalanceBreakdownCard } from '../components/leave-balance-breakdown-card'
import { LeaveBalanceRequestsCard } from '../components/leave-balance-requests-card'
import { useLeaveBalance } from '../hooks/use-leave'
import { useLeaveBalanceAdjustForm } from '../hooks/use-leave-balance-adjust-form'
import type { LeaveBalance } from '../types/leave'

/**
 * CHI TIẾT MỘT DÒNG QUỸ PHÉP — `/hr/leave-balances/:id`.
 *
 * ⚠️ Là một TRANG chứ không phải hộp thoại (đổi 03/09/2026). Bản đầu mở popup
 * «Điều chỉnh quỹ phép» ngay từ dòng, và popup thì buộc phải gói gọn: mọi thứ
 * giải thích cho con số đang sửa — quỹ cấu thành từ đâu, người này đã nghỉ
 * những hôm nào — đều nằm ngoài nó. Người dùng đóng popup ra xem rồi mở lại, và
 * lúc mở lại thì phải nhớ mình vừa đọc gì.
 *
 * Bốn thẻ theo đúng thứ tự người ta hỏi: **quỹ đang thế nào** → **vì sao thế**
 * (những đơn đã nghỉ) → **sửa lại** → **ai đã sửa**. Thẻ sửa đứng gần cuối là cố
 * ý: nó là thao tác nhạy cảm nhất của cả phân hệ (tặng ngày phép cho người
 * khác), nên phải đọc xong hai thẻ trên rồi mới tới.
 *
 * ⚠️ **Dấu vết là thẻ bắt buộc ở màn này**, không phải phần trang trí. Điều
 * chỉnh tay GHI ĐÈ `adjusted_days` chứ không cộng dồn, nên nhìn con số hiện tại
 * không cách nào biết nó đi từ đâu tới và ai đưa nó tới đó — trong khi backend
 * đã ghi sẵn cả câu *"Điều chỉnh quỹ phép: 0 → 3 ngày. Lý do: …"* vào
 * `tab_audit_log` (xem `balance_controller.adjust`). Thiếu thẻ này thì lời hứa
 * "phải truy được ai làm và vì sao" chỉ đúng ở tầng cơ sở dữ liệu.
 */
/**
 * Dòng quỹ RỖNG dùng khi dữ liệu chưa về. Chỉ tồn tại để gọi được hook trạng
 * thái đúng luật (hook không đặt sau `return` sớm); `id: 0` khiến
 * `useHasChanged` nạp lại giá trị thật ngay khi bản ghi về.
 */
const EMPTY_BALANCE: LeaveBalance = {
  id: 0,
  company_id: 0,
  employee_id: 0,
  leave_type_id: 0,
  year: 0,
  allocated_days: 0,
  seniority_days: 0,
  carried_days: 0,
  adjusted_days: 0,
  used_days: 0,
  pending_days: 0,
  remaining_days: 0,
  total_days: 0,
  note: '',
}

export function LeaveBalanceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const balanceId = Number(id) || 0
  const navigate = useNavigate()
  const { can } = usePermission()
  const canAdjust = can('leave_balance', 'write')

  const { data: balance, isLoading } = useLeaveBalance(balanceId)

  //  Gọi vô điều kiện (luật hook), chỉ DỰNG có điều kiện bên dưới. `balance`
  //  chưa về thì đưa dòng rỗng vào — hook chỉ giữ state, không gọi API.
  const adjustForm = useLeaveBalanceAdjustForm(balance ?? EMPTY_BALANCE)

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
        //  ⚠️ Nút Lưu ở ĐẦU TRANG và DÍNH khi cuộn. Trang có bốn thẻ, ô nhập nằm
        //  ở thẻ thứ ba: để nút dưới đáy thẻ đó thì mỗi lần lưu là một lần cuộn
        //  xuống rồi cuộn ngược lên đọc lại con số vừa đổi. Cùng luật với chi
        //  tiết Đơn nghỉ phép.
        sticky
        actions={
          canAdjust ? (
            <Button onClick={adjustForm.submit} disabled={!adjustForm.canSave}>
              <Save className="size-4" />
              Lưu điều chỉnh
            </Button>
          ) : undefined
        }
      />

      <div className="space-y-4">
        <LeaveBalanceBreakdownCard balance={balance} />
        <LeaveBalanceRequestsCard balance={balance} />
        {/*  Chỉ dựng thẻ sửa khi có quyền: hiện form rồi chặn lúc bấm Lưu là
             bắt người ta gõ xong mới biết mình không được phép. */}
        {canAdjust && <LeaveBalanceAdjustCard balance={balance} form={adjustForm} />}

        {/*  `showMessage` BẬT: ở đây câu diễn giải mới là nội dung chính — "ai
             đó bấm Sửa" không nói được gì, "0 → 3 ngày, lý do nghỉ bù Tết" mới
             là thứ người kiểm tra cần. */}
        <AuditTimeline entity="leave_balance" entityId={balance.id} showMessage />
      </div>
    </PageContainer>
  )
}
