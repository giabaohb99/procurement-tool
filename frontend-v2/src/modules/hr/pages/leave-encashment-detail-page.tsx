import { AlertTriangle } from 'lucide-react'
import type { ReactNode } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

import { useAuthStore } from '@/core/auth/auth-store'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { PageContainer } from '@/shared/ui/page-container'
import { LeaveEncashmentDetailActions } from '../components/leave-encashment-detail-actions'
import { LeaveEncashmentFlatShell } from '../components/leave-encashment-flat-shell'
import { LeaveEncashmentForm } from '../components/leave-encashment-form'
import { LeaveEncashmentHistorySections } from '../components/leave-encashment-history-sections'
import { LeaveEncashmentPaymentCard } from '../components/leave-encashment-payment-card'
import { LeaveEncashmentSummary } from '../components/leave-encashment-summary'
import { LeaveStatusBadge } from '../components/leave-status-badge'
import { useLeaveEncashment } from '../hooks/use-leave-encashment'
import { formatEncashDays, getLeaveEncashmentActions, isPayoutRejected } from '../types/leave-encashment'

const ENTITY = 'leave_encashment'

/**
 * CHI TIẾT / LẬP MỚI phiếu thanh toán nghỉ phép (duoc-CR-719) — một trang cho cả hai, phân biệt bằng `:id`
 * (khuôn phiếu nghỉ bù). Bố cục PHẲNG kiểu ERPNext (`LeaveEncashmentFlatShell`): hàng tiêu đề mang mã phiếu + nhãn
 * trạng thái / lý do + mọi nút; dưới là các nhóm Thông tin · Số ngày · Thanh toán · Luồng duyệt · Hoạt động.
 * Còn sửa được (Nháp / Trả về) thì nhóm Thông tin / Số ngày là form; đã gửi thì là bản chỉ xem. Nút hiện theo
 * `getLeaveEncashmentActions` (hàm thuần, có test).
 */
export function LeaveEncashmentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const requestId = Number(id) || 0
  const isNew = requestId === 0
  const navigate = useNavigate()
  const location = useLocation()
  const { can } = usePermission()
  const myEmployeeId = useAuthStore((s) => s.user?.employee_id)

  //  Lùi theo lịch sử để giữ phạm vi / bộ lọc của danh sách; vào thẳng từ link thì mới rơi về danh sách.
  const goBack = () => {
    if (location.key === 'default') navigate(appRoutes.hr.leaveEncashments)
    else navigate(-1)
  }

  const { data: request, isLoading } = useLeaveEncashment(requestId)

  const actions = getLeaveEncashmentActions(request, {
    write: can(ENTITY, 'write'),
    delete: can(ENTITY, 'delete'),
    approve: can(ENTITY, 'approve'),
    cancel: can(ENTITY, 'cancel'),
    isOwnRequest: !!myEmployeeId && request?.employee_id === myEmployeeId,
  })

  if (!isNew && isLoading) return <PageMessage>Đang tải phiếu…</PageMessage>
  if (!isNew && !request) return <PageMessage>Không tìm thấy phiếu thanh toán nghỉ phép này.</PageMessage>
  if (isNew && !can(ENTITY, 'create')) {
    return <PageMessage>Bạn chưa có quyền lập phiếu thanh toán nghỉ phép.</PageMessage>
  }

  const showPayment = Boolean(request && (request.payment_request_id > 0 || request.payment))
  //  Không nút nào thì không dựng cụm — dưới `md` cụm chiếm trọn một hàng, rỗng là một hàng trắng thừa.
  const hasSavedActions = actions.remove || actions.engineDecision || actions.directDecision || actions.cancel
  const savedActions =
    request && hasSavedActions ? <LeaveEncashmentDetailActions request={request} actions={actions} /> : null

  const renderPage = (headerActions: ReactNode, body: ReactNode) => (
    <LeaveEncashmentFlatShell
      title={request ? request.code : 'Lập phiếu thanh toán nghỉ phép'}
      chips={
        request && (
          <>
            <LeaveStatusBadge status={request.status} label={request.status_label} />
            {request.reason_kind_label && <Badge variant="outline">{request.reason_kind_label}</Badge>}
          </>
        )
      }
      actions={headerActions}
      onBack={goBack}
      banner={
        //  D7a: kế toán từ chối YCTT thì phiếu VẪN "Đã duyệt" (ngày đã trừ khỏi quỹ). Phải nói thành lời, không thì
        //  nhân sự thấy nhãn xanh và tin là tiền sắp về.
        isPayoutRejected(request) && (
          <div
            role="status"
            className="flex items-start gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900 md:px-6 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200"
          >
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            <span>
              <strong>Kế toán từ chối chi.</strong> Hủy phiếu để trả lại {formatEncashDays(request?.days ?? 0)} ngày
              phép vào quỹ, rồi lập phiếu mới nếu cần.
            </span>
          </div>
        )
      }
    >
      {body}
      {request && showPayment && (
        <LeaveEncashmentPaymentCard payment={request.payment} cancelBlockedReason={request.cancel_blocked_reason} />
      )}
      {request && <LeaveEncashmentHistorySections request={request} />}
    </LeaveEncashmentFlatShell>
  )

  if (isNew || actions.edit) {
    return (
      //  `key` theo id + updated_at: phiếu vừa bị Trả về / lưu lại thì form nạp lại từ bản mới.
      <LeaveEncashmentForm
        key={request ? `${request.id}-${request.updated_at}` : 'new'}
        request={request}
        onSaved={(savedId) => {
          if (isNew) navigate(appRoutes.hr.leaveEncashmentDetail(savedId), { replace: true })
        }}
        frame={({ actions: formActions, body }) =>
          renderPage(
            <>
              {savedActions}
              {formActions}
            </>,
            body,
          )
        }
      />
    )
  }

  return renderPage(savedActions, request && <LeaveEncashmentSummary request={request} />)
}

function PageMessage({ children }: { children: ReactNode }) {
  return (
    <PageContainer>
      <p className="text-sm text-muted-foreground">{children}</p>
    </PageContainer>
  )
}
