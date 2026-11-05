import { AuditActivityFeed } from '@/shared/audit/audit-activity-feed'
import { FormSection } from '@/shared/ui/form-section'
import type { LeaveEncashment } from '../types/leave-encashment'
import { LeaveCompApprovalTimeline } from './leave-comp-approval-timeline'

interface LeaveEncashmentHistorySectionsProps {
  request: LeaveEncashment
}

/** Nhãn cột cho câu "đã cập nhật ..." của khối Hoạt động — cột không có ở đây bị bỏ khỏi câu. */
const FIELD_LABELS: Record<string, string> = {
  reason_kind: 'Lý do thanh toán',
  days: 'Số ngày thanh toán',
  note: 'Ghi chú',
  status: 'Trạng thái',
}

/**
 * Hai nhóm cuối trang phiếu thanh toán nghỉ phép (duoc-CR-719): LUỒNG DUYỆT và HOẠT ĐỘNG, bố cục phẳng.
 *
 * Luồng duyệt dùng chung `LeaveCompApprovalTimeline` (thẻ của phiếu nghỉ bù) — không sửa thẻ đó, chỉ làm phẳng tại chỗ:
 * khung trang đã gỡ viền / bóng (`ERP_FLATTEN_CARDS`), ở đây ẩn tiêu đề thẻ (nhóm đã có tiêu đề "Luồng duyệt", để lại
 * là nói hai lần) và bỏ đệm dọc của thân thẻ. Kết cục của phiên duyệt vẫn đọc được: nhãn trạng thái phiếu nằm trên
 * hàng tiêu đề trang, phiên bị kẹt có hộp cảnh báo riêng trong thân.
 */
export function LeaveEncashmentHistorySections({ request }: LeaveEncashmentHistorySectionsProps) {
  return (
    <>
      <FormSection title="Luồng duyệt">
        <div className="col-span-full [&_[data-slot=card-content]]:py-0 [&_[data-slot=card-header]]:hidden">
          <LeaveCompApprovalTimeline request={request} />
        </div>
      </FormSection>

      <FormSection title="Hoạt động">
        <div className="col-span-full">
          <AuditActivityFeed
            entity="leave_encashment"
            entityId={request.id}
            fieldLabels={FIELD_LABELS}
            createdNoun="phiếu này"
          />
        </div>
      </FormSection>
    </>
  )
}
