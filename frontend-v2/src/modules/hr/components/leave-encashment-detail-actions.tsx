import { Ban, Check, Trash2, X } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import { useDeleteLeaveEncashment, useLeaveEncashmentAction } from '../hooks/use-leave-encashment'
import { useSingleFlight } from '../hooks/use-single-flight'
import {
  ENCASHMENT_DECISION_REASON_MAX,
  LEAVE_ENCASHMENT_STATUS,
  type getLeaveEncashmentActions,
  type LeaveEncashment,
} from '../types/leave-encashment'
import { PRIMARY_ACTION_SLOT, SECONDARY_ACTION_SLOT } from '../utils/leave-detail-action-slots'
import { LeaveEncashmentDecisionActions } from './leave-encashment-decision-actions'

interface LeaveEncashmentDetailActionsProps {
  request: LeaveEncashment
  /** Kết quả `getLeaveEncashmentActions` (hàm thuần, có test) — trang tính một lần, nút chỉ đọc. */
  actions: ReturnType<typeof getLeaveEncashmentActions>
}

/**
 * Cụm nút của phiếu ĐÃ LƯU trên hàng tiêu đề trang phiếu thanh toán nghỉ phép (duoc-CR-719): Xóa phiếu · duyệt qua
 * bộ máy · Duyệt / Từ chối thẳng · Hủy phiếu, kèm hộp nhập lý do. Tách khỏi trang cho tệp gọn; hành vi giữ nguyên.
 * Cờ `useRef` chung cho xóa / duyệt / từ chối / hủy: `isPending` chỉ đổi ở lần render sau nên không chặn bấm đúp.
 */
export function LeaveEncashmentDetailActions({ request, actions }: LeaveEncashmentDetailActionsProps) {
  const navigate = useNavigate()
  const remove = useDeleteLeaveEncashment()
  const act = useLeaveEncashmentAction()
  const [reasonFor, setReasonFor] = useState<'reject' | 'cancel' | null>(null)
  const runOnce = useSingleFlight()
  const requestId = request.id

  return (
    <>
      {actions.remove && (
        <Button
          type="button"
          variant="outline"
          className={SECONDARY_ACTION_SLOT}
          disabled={remove.isPending}
          onClick={() =>
            runOnce((release) =>
              remove.mutate(requestId, {
                onSuccess: () => navigate(appRoutes.hr.leaveEncashments),
                onSettled: release,
              }),
            )
          }
        >
          <Trash2 className="size-4" />
          Xóa phiếu
        </Button>
      )}

      {actions.engineDecision && <LeaveEncashmentDecisionActions requestId={requestId} />}

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
              runOnce((release) => act.mutate({ id: requestId, action: 'approve' }, { onSettled: release }))
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

      <ReasonConfirmDialog
        open={reasonFor !== null}
        onOpenChange={(open) => !open && setReasonFor(null)}
        title={reasonFor === 'cancel' ? 'Hủy phiếu thanh toán nghỉ phép' : 'Từ chối phiếu thanh toán nghỉ phép'}
        description={
          reasonFor === 'cancel'
            ? request.status === LEAVE_ENCASHMENT_STATUS.APPROVED
              ? 'Số ngày đã thanh toán được trả lại quỹ phép; yêu cầu thanh toán còn Nháp sẽ bị xóa.'
              : 'Phiếu dừng lại, số ngày đang giữ chỗ (nếu có) được trả lại quỹ phép.'
            : 'Người lập sẽ đọc đúng câu này để biết lý do.'
        }
        placeholder={reasonFor === 'cancel' ? 'Vì sao hủy phiếu?' : 'Vì sao không duyệt?'}
        confirmText={reasonFor === 'cancel' ? 'Hủy phiếu' : 'Từ chối'}
        maxLength={ENCASHMENT_DECISION_REASON_MAX}
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
    </>
  )
}
