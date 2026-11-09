import {
  ENCASHMENT_NOTE_MAX,
  LEAVE_ENCASHMENT_REASON,
  validateEncashmentDays,
  type LeaveEncashment,
  type LeaveEncashmentCreatePayload,
  type LeaveEncashmentUpdatePayload,
} from '../types/leave-encashment'

/**
 * Giá trị đang nhập trên form phiếu thanh toán nghỉ phép (duoc-CR-719).
 *
 * `days` giữ CHUỖI người gõ: ô trống là một ý thật — "lấy đúng số được thanh toán lúc lập" (backend nhận `days: null`,
 * kiểu ERPNext tự điền số được phép) — đổi sang số ngay thì ô trống thành `0` và người dùng ăn lỗi "phải lớn hơn 0".
 */
export interface LeaveEncashmentFormValues {
  /** `0` = chính mình. */
  employee_id: number
  /** `0` = chưa chọn. */
  leave_type_id: number
  balance_year: number
  reason_kind: number
  days: string
  note: string
}

export function emptyLeaveEncashmentForm(year: number): LeaveEncashmentFormValues {
  return {
    employee_id: 0,
    leave_type_id: 0,
    balance_year: year,
    reason_kind: LEAVE_ENCASHMENT_REASON.YEAR_END,
    days: '',
    note: '',
  }
}

export function formValuesOfLeaveEncashment(request: LeaveEncashment): LeaveEncashmentFormValues {
  return {
    employee_id: request.employee_id,
    leave_type_id: request.leave_type_id,
    balance_year: request.balance_year,
    reason_kind: request.reason_kind,
    days: request.days ? String(request.days) : '',
    note: request.note ?? '',
  }
}

/** Ô gõ "1,5" hay "1.5" đều là một ngày rưỡi. Trống → `null`. */
export function parseEncashDays(text: string): number | null {
  const trimmed = text.trim()
  if (!trimmed) return null
  return Number(trimmed.replace(',', '.'))
}

export type LeaveEncashmentFormErrors = Partial<Record<'leave_type_id' | 'days' | 'note', string>>

/**
 * Kiểm phía giao diện trước khi gọi API — chỉ để báo sớm; backend vẫn là chốt thật (vượt số được thanh toán, trùng
 * phiếu, thiếu ngày nghỉ việc…). `maxDays` = `encashable` của bản xem trước, `null` khi chưa có (không chặn theo trần).
 *
 * `requireDays` bật khi SỬA phiếu: PATCH với `days: null` nghĩa là "giữ số cũ" chứ không phải "lấy số được phép",
 * nên ô trống lúc sửa là mơ hồ — bắt nhập.
 */
export function validateLeaveEncashmentForm(
  values: LeaveEncashmentFormValues,
  maxDays: number | null,
  requireDays = false,
): LeaveEncashmentFormErrors {
  const errors: LeaveEncashmentFormErrors = {}
  if (!values.leave_type_id) errors.leave_type_id = 'Chọn loại nghỉ cần thanh toán.'
  const days = parseEncashDays(values.days)
  if (days === null && requireDays) {
    errors.days = 'Nhập số ngày thanh toán.'
  } else if (days === null) {
    //  Ô trống = lấy số được phép; nếu số đó là 0 thì không có gì để lập phiếu.
    if (maxDays !== null && maxDays <= 0) errors.days = 'Không còn ngày nào được thanh toán.'
  } else {
    const message = validateEncashmentDays(days, maxDays)
    if (message) errors.days = message
  }
  if (values.note.length > ENCASHMENT_NOTE_MAX) errors.note = `Ghi chú tối đa ${ENCASHMENT_NOTE_MAX} ký tự.`
  return errors
}

export function toLeaveEncashmentCreatePayload(
  values: LeaveEncashmentFormValues,
): LeaveEncashmentCreatePayload {
  return {
    employee_id: values.employee_id || 0,
    leave_type_id: values.leave_type_id,
    balance_year: values.balance_year,
    reason_kind: values.reason_kind,
    days: parseEncashDays(values.days),
    note: values.note.trim(),
  }
}

/** Sửa: người, loại nghỉ, năm quỹ không đổi được (backend bỏ qua) — chỉ gửi ba ô này. */
export function toLeaveEncashmentUpdatePayload(
  values: LeaveEncashmentFormValues,
): LeaveEncashmentUpdatePayload {
  return {
    reason_kind: values.reason_kind,
    days: parseEncashDays(values.days),
    note: values.note.trim(),
  }
}
