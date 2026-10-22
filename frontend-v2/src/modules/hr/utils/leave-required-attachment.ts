import type { LeaveType } from '../types/leave'
import type { LeaveLineValue } from './leave-form-values'

/**
 * Tên các loại nghỉ TRONG ĐƠN đang bật «Bắt buộc đính kèm» (duoc-CR-661).
 *
 * Khớp luật backend `request_service.check_required_attachment`: đơn nhiều loại
 * chỉ cần MỘT loại bật cờ là phải có tệp. Dòng chưa chọn loại (`0`) bỏ qua.
 * Trả mảng rỗng = đơn không đòi tệp.
 */
export function listTypesRequiringAttachment(
  lines: LeaveLineValue[],
  types: Pick<LeaveType, 'id' | 'name' | 'require_attachment'>[],
): string[] {
  const chosen = new Set(lines.map((line) => line.leave_type_id).filter((id) => id > 0))
  return types.filter((t) => chosen.has(t.id) && t.require_attachment).map((t) => t.name)
}
