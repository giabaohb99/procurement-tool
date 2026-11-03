import {
  COMP_REASON_MAX,
  LEAVE_COMP_DAY_OPTIONS,
  type LeaveCompPayload,
  type LeaveCompRequest,
} from '../types/leave-comp'

/** Giá trị đang nhập trên form phiếu nghỉ bù. `days` luôn là số (0.5 | 1). */
export interface LeaveCompFormValues {
  /** `0` = chính mình. */
  employee_id: number
  work_date: string
  days: number
  reason: string
}

export function emptyLeaveCompForm(): LeaveCompFormValues {
  return { employee_id: 0, work_date: '', days: 1, reason: '' }
}

export function formValuesOfLeaveComp(request: LeaveCompRequest): LeaveCompFormValues {
  return {
    employee_id: request.employee_id,
    work_date: request.work_date,
    days: request.days,
    reason: request.reason ?? '',
  }
}

/** Tiêu đề lỗi theo ô; rỗng = hợp lệ. */
export type LeaveCompFormErrors = Partial<Record<'work_date' | 'days' | 'reason', string>>

/**
 * Kiểm phía giao diện trước khi gọi API — chỉ để báo sớm, backend vẫn là chốt thật
 * (ngày tương lai, ngày làm việc thường, trùng phiếu đều do backend phán).
 *
 * `today` truyền vào (`yyyy-mm-dd`) thay vì đọc đồng hồ: hàm thuần, test không phụ thuộc hôm nay.
 * `requireReason` bật ở «Gửi duyệt» — lưu nháp cho để trống lý do.
 */
export function validateLeaveCompForm(
  values: LeaveCompFormValues,
  today: string,
  requireReason: boolean,
): LeaveCompFormErrors {
  const errors: LeaveCompFormErrors = {}
  if (!values.work_date) errors.work_date = 'Chọn ngày đã đi làm.'
  //  So chuỗi `yyyy-mm-dd` trùng thứ tự thời gian.
  else if (values.work_date > today) errors.work_date = 'Ngày đi làm không được ở tương lai.'
  if (!(LEAVE_COMP_DAY_OPTIONS as readonly number[]).includes(values.days)) {
    errors.days = 'Số ngày chỉ nhận 0,5 hoặc 1.'
  }
  const reason = values.reason.trim()
  if (requireReason && !reason) errors.reason = 'Nhập lý do đi làm để người duyệt nắm.'
  else if (values.reason.length > COMP_REASON_MAX) {
    errors.reason = `Lý do tối đa ${COMP_REASON_MAX} ký tự.`
  }
  return errors
}

export function toLeaveCompPayload(values: LeaveCompFormValues): LeaveCompPayload {
  return {
    employee_id: values.employee_id || 0,
    work_date: values.work_date,
    days: values.days,
    reason: values.reason.trim(),
  }
}
