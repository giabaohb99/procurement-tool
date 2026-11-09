import { FormSection } from '@/shared/ui/form-section'
import { formatDateTime } from '@/shared/utils/format-date'
import { formatEncashDays, type LeaveEncashment } from '../types/leave-encashment'
import { EncashReadOnlyField } from './leave-encashment-flat-field'

interface LeaveEncashmentSummaryProps {
  request: LeaveEncashment
}

/**
 * BẢN CHỈ XEM của phiếu thanh toán nghỉ phép (đã gửi duyệt) — bố cục phẳng: hai nhóm Thông tin / Số ngày, cùng lưới
 * 2 cột và cùng hàng nhãn với form để mở phiếu Nháp hay phiếu đã gửi đều thấy một dáng. Ô chỉ xem là hộp chữ (bôi đen
 * được), không dựng form với `disabled`.
 */
export function LeaveEncashmentSummary({ request }: LeaveEncashmentSummaryProps) {
  const note = request.note?.trim()
  const decisionNote = request.decision_note?.trim()
  return (
    <>
      <FormSection title="Thông tin">
        <EncashReadOnlyField label="Người được thanh toán">
          {(request.employee_name || `#${request.employee_id}`) +
            (request.employee_code ? ` (${request.employee_code})` : '')}
        </EncashReadOnlyField>
        <EncashReadOnlyField label="Phòng ban">{request.department_name?.trim() || '—'}</EncashReadOnlyField>
        <EncashReadOnlyField label="Loại nghỉ">{request.leave_type_name}</EncashReadOnlyField>
        <EncashReadOnlyField label="Năm quỹ phép">{request.balance_year}</EncashReadOnlyField>
        <EncashReadOnlyField label="Lý do thanh toán">{request.reason_kind_label}</EncashReadOnlyField>
        {request.decided_at && (
          <EncashReadOnlyField label="Chốt lúc">{formatDateTime(request.decided_at)}</EncashReadOnlyField>
        )}
        <EncashReadOnlyField label="Ghi chú" full multiline>
          {note || '—'}
        </EncashReadOnlyField>
        {decisionNote && (
          <EncashReadOnlyField label="Ghi chú của người chốt" full multiline>
            {decisionNote}
          </EncashReadOnlyField>
        )}
      </FormSection>

      <FormSection title="Số ngày">
        <EncashReadOnlyField label="Số ngày thanh toán">{`${formatEncashDays(request.days)} ngày`}</EncashReadOnlyField>
        {request.encashable_snapshot > 0 && (
          <EncashReadOnlyField label="Lúc gửi duyệt">
            {`Còn dùng được ${formatEncashDays(request.balance_snapshot)} ngày, được thanh toán tối đa ${formatEncashDays(request.encashable_snapshot)} ngày`}
          </EncashReadOnlyField>
        )}
      </FormSection>
    </>
  )
}
