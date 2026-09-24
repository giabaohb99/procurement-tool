/**
 * «Phòng xử lý» của YCMH · YCBG · ĐMH — bao-CR-480.
 *
 * Một ô, một cách gọi ở cả ba chứng từ: phòng nào sẽ đi mua cho phiếu này. Giá trị `0`
 * là «Thu mua chung»; nhà máy tự mua thì là chính phòng nhà máy (backend tự điền lúc lập
 * phiếu cho phòng có bộ máy mua riêng). Trước CR này ô tên «Nhờ phòng xử lý», giá trị
 * rỗng in «Không nhờ» — người dùng đọc không hiểu «không nhờ» thì ai mua, và màn ĐMH
 * không có ô này nên mở đơn nhà máy mua hộ phòng khác không thấy ai đang mua.
 */
import type { Department } from '@/modules/hr/types/department'

export const SHARED_PURCHASING_LABEL = 'Thu mua chung'

/** Câu gợi ý dưới ô — nói bằng việc, không nói bằng cột dữ liệu. */
export const HANDLING_DEPT_HINT =
  'Phòng sẽ đi mua cho phiếu này. Mặc định là Thu mua chung; phòng có bộ máy mua riêng (nhà máy) thì hệ thống tự chọn phòng của người yêu cầu.'

/**
 * Nhãn hiển thị của phòng xử lý. Ưu tiên tên backend trả kèm (`handler_dept_name`) — không
 * cần quyền đọc danh mục phòng ban; thiếu thì tra danh mục đã nạp; cuối cùng mới in số id
 * (phòng đã bị xóa khỏi danh mục).
 */
export function handlingDeptLabel(
  handlerDeptId: number | null | undefined,
  handlerDeptName?: string | null,
  departments: Pick<Department, 'id' | 'name'>[] = [],
): string {
  const id = Number(handlerDeptId) || 0
  if (!id) return SHARED_PURCHASING_LABEL
  const name = (handlerDeptName || '').trim() || departments.find((d) => d.id === id)?.name || ''
  return name || `Phòng #${id}`
}

/**
 * Mục chọn cho ô Phòng xử lý: «Thu mua chung» đứng đầu (giá trị '0'), rồi phòng đang
 * hoạt động; phòng đã tắt nhưng phiếu cũ còn trỏ tới thì giữ lại để không mất nhãn.
 */
export function handlingDeptOptions(
  departments: Pick<Department, 'id' | 'name' | 'is_active'>[],
  currentId: number | null | undefined,
): { value: string; label: string }[] {
  const current = Number(currentId) || 0
  return [
    { value: '0', label: SHARED_PURCHASING_LABEL },
    ...departments
      .filter((d) => d.is_active !== false || d.id === current)
      .map((d) => ({ value: String(d.id), label: d.name })),
  ]
}
