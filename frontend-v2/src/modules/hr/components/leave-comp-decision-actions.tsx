import type { ApprovalDecision } from '../hooks/use-leave'
import { useLeaveCompToApprove } from '../hooks/use-leave-comp'
import { LeaveEngineDecisionActions, type EngineDecisionFace } from './leave-engine-decision-actions'

interface LeaveCompDecisionActionsProps {
  requestId: number
}

const FACES: Record<ApprovalDecision, EngineDecisionFace> = {
  approve: {
    title: 'Duyệt phiếu nghỉ bù',
    description: 'Duyệt xong, số ngày được cộng thêm vào quỹ phép của người nghỉ (nếu hết các chặng).',
    placeholder: 'Ý kiến (không bắt buộc)',
    confirm: 'Duyệt',
    optional: true,
  },
  return: {
    title: 'Trả phiếu về chỉnh sửa',
    description: 'Người lập sẽ đọc đúng câu này để biết phải sửa gì.',
    placeholder: 'Cần sửa gì?',
    confirm: 'Trả về',
    optional: false,
  },
  reject: {
    title: 'Từ chối phiếu nghỉ bù',
    description: 'Phiếu dừng lại, quỹ phép không đổi.',
    placeholder: 'Vì sao không duyệt?',
    confirm: 'Từ chối',
    optional: false,
  },
}

/**
 * Ba nút duyệt qua BỘ MÁY trên trang chi tiết phiếu nghỉ bù — khung dùng chung ở `LeaveEngineDecisionActions`.
 *
 * ⚠️ Điều kiện hiện nút là "có việc treo của TÔI trên phiếu này" (đọc từ `/to-approve`), không phải
 * "có quyền approve" — cùng luật với `LeaveDetailDecisionActions`.
 */
export function LeaveCompDecisionActions({ requestId }: LeaveCompDecisionActionsProps) {
  const { data } = useLeaveCompToApprove(requestId > 0)
  const row = data?.items.find((item) => item.id === requestId)
  return <LeaveEngineDecisionActions instanceId={row?.task.instance_id} faces={FACES} />
}
