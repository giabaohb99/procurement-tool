import { ArrowLeft, Ban, Check, Trash2, X } from 'lucide-react'
import { useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import { formatDate } from '@/shared/utils/format-date'
import { LeaveCompApprovalTimeline } from '../components/leave-comp-approval-timeline'
import { LeaveCompDecisionActions } from '../components/leave-comp-decision-actions'
import { LeaveCompRequestForm } from '../components/leave-comp-request-form'
import { LeaveCompRequestSummary } from '../components/leave-comp-request-summary'
import { LeaveStatusBadge } from '../components/leave-status-badge'
import {
  useDeleteLeaveCompRequest,
  useLeaveCompAction,
  useLeaveCompRequest,
} from '../hooks/use-leave-comp'
import { useSingleFlight } from '../hooks/use-single-flight'
import { COMP_DECISION_REASON_MAX, getLeaveCompActions } from '../types/leave-comp'
import { PRIMARY_ACTION_SLOT, SECONDARY_ACTION_SLOT } from '../utils/leave-detail-action-slots'

const ENTITY = 'leave_comp_request'

/**
 * CHI TIẾT / LẬP MỚI phiếu xin nghỉ bù — một trang cho cả hai, phân biệt bằng `:id` (khuôn đơn nghỉ phép).
 *
 * Còn sửa được (Nháp / Trả về) thì dựng `LeaveCompRequestForm`; đã gửi duyệt thì dựng bản chỉ xem.
 * Nút hiện theo `getLeaveCompActions` (hàm thuần, có test) — gồm luật "đang có phiên duyệt chạy thì
 * ẩn Duyệt thẳng".
 */
export function LeaveCompRequestDetailPage() {
  const { id } = useParams<{ id: string }>()
  const requestId = Number(id) || 0
  const isNew = requestId === 0
  const navigate = useNavigate()
  const location = useLocation()
  const { can } = usePermission()

  //  Lùi theo lịch sử để giữ tab / bộ lọc của danh sách; vào thẳng từ link thì mới rơi về danh sách.
  const goBack = () => {
    if (location.key === 'default') navigate(appRoutes.hr.leaveCompRequests)
    else navigate(-1)
  }

  const { data: request, isLoading } = useLeaveCompRequest(requestId)
  const remove = useDeleteLeaveCompRequest()
  const act = useLeaveCompAction()
  const [reasonFor, setReasonFor] = useState<'reject' | 'cancel' | null>(null)
  //  Cờ `useRef` chung cho xóa / duyệt / từ chối / hủy: `isPending` chỉ đổi ở lần render sau nên không chặn được bấm đúp.
  const runOnce = useSingleFlight()

  const actions = getLeaveCompActions(request, {
    write: can(ENTITY, 'write'),
    delete: can(ENTITY, 'delete'),
    approve: can(ENTITY, 'approve'),
    cancel: can(ENTITY, 'cancel'),
  })

  if (!isNew && isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Đang tải phiếu…</p>
      </PageContainer>
    )
  }
  if (!isNew && !request) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Không tìm thấy phiếu nghỉ bù này.</p>
      </PageContainer>
    )
  }
  if (isNew && !can(ENTITY, 'create')) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Bạn chưa có quyền lập phiếu nghỉ bù.</p>
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader
        sticky
        leading={
          <Button
            type="button"
            variant="outline"
            size="icon"
            title="Về danh sách"
            aria-label="Về danh sách"
            onClick={goBack}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
        title={isNew ? 'Lập phiếu nghỉ bù' : `Phiếu nghỉ bù ${request?.code}`}
        description={
          request ? (
            <>
              <LeaveStatusBadge status={request.status} label={request.status_label} />
              <span>
                {request.employee_name} · làm ngày {formatDate(request.work_date)}
              </span>
            </>
          ) : (
            'Đi làm vào ngày nghỉ thì xin cộng ngày nghỉ bù vào quỹ phép.'
          )
        }
        actions={
          <div className="flex w-full flex-wrap items-center gap-2 md:w-auto md:justify-end">
            {actions.remove && (
              <Button
                type="button"
                variant="outline"
                className={SECONDARY_ACTION_SLOT}
                disabled={remove.isPending}
                onClick={() =>
                  runOnce((release) =>
                    remove.mutate(requestId, {
                      onSuccess: () => navigate(appRoutes.hr.leaveCompRequests),
                      onSettled: release,
                    }),
                  )
                }
              >
                <Trash2 className="size-4" />
                Xóa phiếu
              </Button>
            )}

            {request && actions.engineDecision && <LeaveCompDecisionActions requestId={requestId} />}

            {actions.directDecision && (
              <>
                <Button
                  type="button"
                  variant="outline"
                  className={SECONDARY_ACTION_SLOT}
                  disabled={act.isPending}
                  onClick={() => setReasonFor('reject')}
                >
                  <X className="size-4" />
                  Từ chối
                </Button>
                <Button
                  type="button"
                  className={PRIMARY_ACTION_SLOT}
                  disabled={act.isPending}
                  onClick={() =>
                    runOnce((release) =>
                      act.mutate({ id: requestId, action: 'approve' }, { onSettled: release }),
                    )
                  }
                >
                  <Check className="size-4" />
                  Duyệt phiếu
                </Button>
              </>
            )}

            {actions.cancel && (
              <Button
                type="button"
                variant="outline"
                className={SECONDARY_ACTION_SLOT}
                disabled={act.isPending}
                onClick={() => setReasonFor('cancel')}
              >
                <Ban className="size-4" />
                Hủy phiếu
              </Button>
            )}
          </div>
        }
      />

      <div className="space-y-4">
        {isNew || actions.edit ? (
          //  `key` theo id + updated_at: phiếu vừa bị Trả về / lưu lại thì form nạp lại từ bản mới.
          <LeaveCompRequestForm
            key={request ? `${request.id}-${request.updated_at}` : 'new'}
            request={request}
            onSaved={(savedId) => {
              if (isNew) navigate(appRoutes.hr.leaveCompRequestDetail(savedId), { replace: true })
            }}
          />
        ) : (
          request && <LeaveCompRequestSummary request={request} />
        )}

        {request && <LeaveCompApprovalTimeline request={request} />}
      </div>

      <ReasonConfirmDialog
        open={reasonFor !== null}
        onOpenChange={(open) => !open && setReasonFor(null)}
        title={reasonFor === 'cancel' ? 'Hủy phiếu nghỉ bù' : 'Từ chối phiếu nghỉ bù'}
        description={
          reasonFor === 'cancel'
            ? 'Phiếu dừng lại. Nếu đã duyệt, số ngày đã cộng sẽ bị trừ lại khỏi quỹ — không hủy được khi người nghỉ đã dùng hết phần đó.'
            : 'Người lập sẽ đọc đúng câu này để biết lý do.'
        }
        placeholder={reasonFor === 'cancel' ? 'Vì sao hủy phiếu?' : 'Vì sao không duyệt?'}
        confirmText={reasonFor === 'cancel' ? 'Hủy phiếu' : 'Từ chối'}
        maxLength={COMP_DECISION_REASON_MAX}
        destructive
        pending={act.isPending}
        onConfirm={(reason) => {
          if (!reasonFor) return
          runOnce((release) =>
            act.mutate(
              { id: requestId, action: reasonFor, reason },
              { onSuccess: () => setReasonFor(null), onSettled: release },
            ),
          )
        }}
      />
    </PageContainer>
  )
}
