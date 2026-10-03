/**
 * «Phòng xử lý» của YCMH · YCBG · ĐMH — bao-CR-480, đổi ở bao-CR-524.
 *
 * Một ô, một cách gọi ở cả ba chứng từ: phòng nào sẽ đi mua cho phiếu này. Nhà máy tự mua thì
 * là chính phòng nhà máy (backend tự điền lúc lập phiếu cho phòng có bộ máy mua riêng).
 *
 * bao-CR-524 (khách chốt 30/09/2026): KHÔNG còn mục ảo «Thu mua chung» (giá trị `0`). Phòng thu
 * mua mặc định là một PHÒNG THẬT trong danh mục (mã cấu hình được, mặc định PBA017 «Sản xuất
 * -Thu mua»), backend tự ghi id thật khi phiếu không nhờ phòng nào và trả kèm tên phòng — kể cả
 * phiếu cũ còn `0`. Giao diện vì thế chỉ bày danh mục phòng ban, không tự chế mục nào.
 */
import type { Department } from '@/modules/hr/types/department'

/**
 * Nhãn dự phòng khi phiếu không mang phòng nào mà backend cũng không trả được tên — chỉ xảy ra
 * khi danh mục chưa có phòng thu mua mặc định. Không phải một mục chọn.
 */
export const DEFAULT_PURCHASING_LABEL = 'Phòng thu mua mặc định'

/** bao-CR-488 — nhãn ô tick lúc lập phiếu; tick mới bung ô chọn phòng. */
export const ASSIGN_OTHER_DEPT_LABEL = 'Nhờ phòng khác xử lý'

/** Câu gợi ý dưới ô — nói bằng việc, không nói bằng cột dữ liệu. */
export const HANDLING_DEPT_HINT =
  'Phòng sẽ đi mua cho phiếu này. Mặc định là phòng thu mua (Sản xuất -Thu mua); phòng có bộ máy mua riêng (nhà máy) thì hệ thống tự chọn phòng của người yêu cầu.'

/** Chữ mờ của ô chọn khi chưa chọn phòng nào — để trống thì backend ghi phòng thu mua mặc định. */
export const HANDLING_DEPT_PLACEHOLDER = 'Để trống = phòng thu mua mặc định'

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
  const name = (handlerDeptName || '').trim() || departments.find((d) => d.id === id)?.name || ''
  if (name) return name
  return id ? `Phòng #${id}` : DEFAULT_PURCHASING_LABEL
}

type HandlingDeptDraft = { handler_dept_id?: number | null; handler_dept_assigned?: boolean }

/**
 * bao-CR-488 — lúc LẬP phiếu, ô «Phòng xử lý» ẩn sau ô tick «Nhờ phòng khác xử lý». Người dùng
 * chưa đụng ô tick thì suy từ dữ liệu: bản nháp chép từ phiếu nguồn đã có phòng xử lý (YCBG
 * tạo từ YCMH) thì coi như đã tick, để không âm thầm rơi mất phòng đó.
 */
export function isHandlingDeptAssigned(draft: HandlingDeptDraft): boolean {
  if (typeof draft.handler_dept_assigned === 'boolean') return draft.handler_dept_assigned
  return (Number(draft.handler_dept_id) || 0) > 0
}

/**
 * Giá trị `handler_dept_id` gửi lên khi TẠO phiếu: không tick → `undefined` (KHÔNG gửi, backend
 * tự chọn mặc định: nhà máy → chính phòng mình, còn lại → phòng thu mua mặc định); tick → số đã
 * chọn. Tick mà để trống thì gửi `0` — backend hiểu là nhờ phòng thu mua mặc định và ghi id thật
 * (bao-CR-524), đó là lựa chọn có chủ ý, không bị tra đè như khi không tick.
 */
export function handlingDeptForCreate(draft: HandlingDeptDraft): number | undefined {
  return isHandlingDeptAssigned(draft) ? Number(draft.handler_dept_id) || 0 : undefined
}

/**
 * 03/10/2026 — lúc LẬP YCMH bỏ ô tick «Nhờ phòng khác xử lý»: chỉ còn MỘT ô chọn, mặc định hiện
 * «Phòng thu mua mặc định», bấm vào mới xổ danh mục phòng ban.
 *
 * ⚠️ Mục mặc định KHÔNG phải phòng `0` hay một phòng cụ thể — nó là trạng thái «CHƯA nhờ»
 * (`handler_dept_assigned = false`), để `handlingDeptForCreate` KHÔNG gửi gì và backend tự chọn:
 * người nhà máy → chính phòng nhà máy, còn lại → phòng thu mua mặc định. Quy nó về `0` là ép
 * mọi phiếu nhà máy sang thu mua chung. Muốn nhờ hẳn phòng thu mua thì chọn phòng thật
 * «Sản xuất -Thu mua» trong danh sách. Khóa chuỗi riêng (không phải `'0'`) để không lẫn với id.
 */
export const HANDLING_DEPT_DEFAULT_OPTION = 'default'

/** Mục chọn lúc LẬP phiếu: «Phòng thu mua mặc định» đứng đầu, sau đó là danh mục phòng ban. */
export function handlingDeptCreateOptions(
  departments: Pick<Department, 'id' | 'name' | 'is_active'>[],
  currentId: number | null | undefined,
): { value: string; label: string }[] {
  return [
    { value: HANDLING_DEPT_DEFAULT_OPTION, label: DEFAULT_PURCHASING_LABEL },
    ...handlingDeptOptions(departments, currentId),
  ]
}

/** Giá trị đang chọn lúc LẬP phiếu — chưa nhờ phòng nào (hoặc nhờ mà để trống) thì là mục mặc định. */
export function handlingDeptCreateValue(draft: HandlingDeptDraft): string {
  const id = Number(draft.handler_dept_id) || 0
  return isHandlingDeptAssigned(draft) && id > 0 ? String(id) : HANDLING_DEPT_DEFAULT_OPTION
}

/** Đổi lựa chọn lúc LẬP phiếu thành phần cập nhật bản nháp (xem `HANDLING_DEPT_DEFAULT_OPTION`). */
export function handlingDeptCreateChange(value: string): {
  handler_dept_assigned: boolean
  handler_dept_id: number
} {
  const id = Number(value) || 0
  if (value === HANDLING_DEPT_DEFAULT_OPTION || id <= 0) {
    return { handler_dept_assigned: false, handler_dept_id: 0 }
  }
  return { handler_dept_assigned: true, handler_dept_id: id }
}

/**
 * Mục chọn cho ô Phòng xử lý: phòng đang hoạt động trong danh mục — KHÔNG có mục ảo nào (bao-CR-524
 * bỏ «Thu mua chung» giá trị `0`); phòng đã tắt nhưng phiếu cũ còn trỏ tới thì giữ lại để không
 * mất nhãn.
 */
export function handlingDeptOptions(
  departments: Pick<Department, 'id' | 'name' | 'is_active'>[],
  currentId: number | null | undefined,
): { value: string; label: string }[] {
  const current = Number(currentId) || 0
  return departments
    .filter((d) => d.is_active !== false || d.id === current)
    .map((d) => ({ value: String(d.id), label: d.name }))
}
