import type { SearchSelectOption } from '@/shared/ui/search-select'
import type { BookingPickOptions } from '../types/vehicle-booking'

/**
 * Hai ô «Công ty» + «Người duyệt» của phiếu đặt xe (duoc-CR-681) — hàm thuần để kiểm được.
 *
 * Hai ô ĐỘC LẬP: đổi công ty không lọc người duyệt và ngược lại (anh Được chốt 23/10/2026).
 */

/** Ô công ty: tên + MST. Công ty đã lưu trên phiếu mà nay ngừng dùng thì vẫn bày để ô không trống. */
export function companySelectOptions(
  data: BookingPickOptions | undefined,
  savedId: number,
  savedName: string,
): SearchSelectOption[] {
  const options: SearchSelectOption[] = (data?.companies ?? []).map((c) => ({
    value: String(c.id),
    label: c.name,
    hint: c.tax_code ? `MST ${c.tax_code}` : '',
    avatar: c.logo ?? '',
  }))
  if (savedId && !options.some((o) => o.value === String(savedId))) {
    options.push({
      value: String(savedId),
      label: `${savedName || `Công ty #${savedId}`} (đã ngừng dùng)`,
      avatar: '',
    })
  }
  return options
}

/**
 * Ô người duyệt: tên · mã · vai trò. Bỏ chính người đang lập phiếu (backend chặn tự chọn mình — bày ra
 * rồi mới báo lỗi lúc gửi là bẫy). Người đã chọn mà nay mất quyền thì bày kèm cảnh báo, không giấu.
 */
export function approverSelectOptions(
  data: BookingPickOptions | undefined,
  savedUserId: number,
  savedName: string,
  selfUserId = 0,
): SearchSelectOption[] {
  const options: SearchSelectOption[] = (data?.approvers ?? [])
    .filter((a) => !selfUserId || a.user_id !== selfUserId)
    .map((a) => ({
      value: String(a.user_id),
      //  «Mã - Tên» như mẫu anh Được gửi 24/10/2026; dòng phụ = vai trò cấp quyền duyệt (kèm phạm vi).
      label: a.code ? `${a.code} - ${a.name}` : a.name,
      hint: a.roles.map((r) => `${r.role} (${r.scope_label})`).join(', '),
      avatar: a.avatar ?? '',
    }))
  if (savedUserId && data && !options.some((o) => o.value === String(savedUserId))) {
    options.push({
      value: String(savedUserId),
      label: `${savedName || `Tài khoản #${savedUserId}`} (không còn quyền duyệt — chọn lại)`,
      avatar: '',
    })
  }
  return options
}

/** Công ty ban đầu: phiếu đang sửa / nhân bản giữ công ty của nó, phiếu mới lấy pháp nhân của người tạo. */
export function initialCompanyId(sourceCompanyId: number | undefined, data: BookingPickOptions | undefined): number {
  return sourceCompanyId || data?.default_company_id || 0
}

/**
 * Câu chặn lúc GỬI DUYỆT (lưu nháp không chặn). Người duyệt bắt buộc và phải còn trong danh sách —
 * backend cũng chặn (422) nhưng báo ngay tại form thì người dùng biết sửa ô nào.
 */
export function pickValidationMessage(
  data: BookingPickOptions | undefined,
  companyId: number,
  approverUserId: number,
): string {
  if (!approverUserId) return 'Vui lòng chọn người phê duyệt.'
  if (!companyId) return 'Vui lòng chọn công ty.'
  if (data && !data.approvers.some((a) => a.user_id === approverUserId)) {
    return 'Người duyệt đã chọn không còn quyền duyệt phiếu đặt xe — vui lòng chọn lại.'
  }
  return ''
}
