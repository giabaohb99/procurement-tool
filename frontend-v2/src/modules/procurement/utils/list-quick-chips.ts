import type { AuthUser } from '@/core/auth/auth-types'
import type { ListParams } from '@/shared/types/api'

/**
 * Hàm thuần của CHIP LỌC NHANH trên bốn màn danh sách Thu mua (kh-NT2-2, doc
 * `erp/nen-tang/14` §2).
 *
 * Chip không có trạng thái riêng: bấm chip là ghi vào ĐÚNG tham số lọc mà ô chọn /
 * ô ngày bên cạnh đang dùng, và chip sáng khi tham số đó mang đúng giá trị của chip.
 * Nhờ vậy chip với ô lọc không bao giờ nói hai điều khác nhau.
 */

export type DateRange = [string, string]

/** Lời giải thích khi chip *Của tôi* mờ — dùng chung bốn màn. */
export const NO_EMPLOYEE_REASON =
  'Tài khoản chưa gắn hồ sơ nhân sự nên không biết phiếu nào là của bạn'

/** Khoảng đang đặt có trùng KHỚP CẢ HAI ĐẦU với khoảng của chip không. */
export function isSameRange(from: string, to: string, range: DateRange): boolean {
  return from === range[0] && to === range[1]
}

/**
 * Bấm chip ngày: đang đúng khoảng của chip thì tắt (trả hai chuỗi rỗng), còn lại —
 * kể cả khi đang có một khoảng KHÁC — thì đặt khoảng của chip.
 */
export function toggleRange(from: string, to: string, range: DateRange): DateRange {
  return isSameRange(from, to, range) ? ['', ''] : range
}

/** Mã nhân sự (NSU...) của người đăng nhập — cột `assignee` trên dòng YCMH / YCBG lưu mã. */
export function resolveMyEmployeeCode(user: AuthUser | null): string | null {
  const code = (user?.emp_code ?? '').trim()
  return code || null
}

/**
 * ID nhân sự của người đăng nhập, dạng chuỗi cho tham số URL — `nspt_id` trên ĐMH là
 * ID nhân sự, không phải mã. `0` nghĩa là chưa gắn nhân sự.
 */
export function resolveMyEmployeeId(user: AuthUser | null): string | null {
  const id = user?.employee_id ?? 0
  return id > 0 ? String(id) : null
}

/**
 * Tên nhân sự của người đăng nhập — `Survey.nspt` lưu TÊN người tạo phiếu.
 *
 * ⚠️ Tài khoản chưa gắn nhân sự thì `/api/auth/me` trả `full_name` = email; lọc theo
 * đó là bảng rỗng mà không ai hiểu vì sao, nên phải có `employee_id` mới tính.
 */
export function resolveMyEmployeeName(user: AuthUser | null): string | null {
  if (!resolveMyEmployeeId(user)) return null
  const name = (user?.full_name ?? '').trim()
  return name || null
}

/**
 * Bộ tham số cho MỘT lượt `useSetUrlParams` của nút *Xóa lọc*: xóa các ô lọc nhanh
 * `keys`, và nếu `withAdvanced` thì xóa luôn điều kiện nâng cao (`<cột>__<op>`,
 * `conjunction`) đang có trong `searchParams`.
 *
 * ⚠️ Vì sao phải gom một lượt: `setSearchParams(fn)` của react-router đưa cho `fn`
 * URL LÚC DỰNG, không phải URL vừa ghi. Gọi mười setter liền nhau thì chỉ lần cuối
 * ăn — nút *Xóa lọc* cũ của bốn màn này chỉ xóa đúng một ô cuối danh sách, và bản
 * nhớ bộ lọc (kh-NT2-2) giữ nguyên mấy ô còn lại cho lần mở sau.
 */
export function buildClearParams(
  keys: string[],
  searchParams: URLSearchParams,
  withAdvanced = false,
): Record<string, null> {
  const cleared: Record<string, null> = {}
  for (const key of keys) cleared[key] = null
  if (withAdvanced) {
    for (const key of searchParams.keys()) {
      if (key.includes('__') || key === 'conjunction') cleared[key] = null
    }
  }
  return cleared
}

/** Giá trị không khớp mã nào — gửi khi hai điều kiện IN cùng cột không giao nhau. */
const MATCH_NOTHING = '__none__'

/**
 * Thêm điều kiện `<field>__in=<values>` của chip vào bộ tham số đã dựng từ bộ lọc
 * nâng cao. Trả `false` khi không ghép được.
 *
 * - Bộ lọc nâng cao đã có `<field>__in`: giữ PHẦN GIAO (hai điều kiện nối AND),
 *   không ghi đè. Giao rỗng thì gửi giá trị không khớp gì, chứ gửi chuỗi rỗng là máy
 *   chủ bỏ điều kiện và trả cả tập.
 * - Bộ lọc nâng cao đang nối bằng OR: máy chủ nối MỌI tham số có hậu tố bằng
 *   `conjunction`, thêm vào là chip thành "HOẶC đang chờ xử lý" — bảng ra nhiều hơn
 *   chứ không ít đi. Nên không ghép, để màn làm mờ chip.
 */
export function addInCondition(params: ListParams, field: string, values: string[]): boolean {
  if (params.conjunction === 'or') return false
  const key = `${field}__in`
  const existing = params[key]
  if (existing === undefined || existing === '') {
    params[key] = values.join(',')
    return true
  }
  const allowed = new Set(String(existing).split(','))
  const overlap = values.filter((value) => allowed.has(value))
  params[key] = overlap.length ? overlap.join(',') : MATCH_NOTHING
  return true
}
