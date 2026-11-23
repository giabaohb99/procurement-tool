/**
 * duoc-CR-784 — chip lọc theo NHÓM của bảng "Mã đã chọn" (Tất cả · Chai · Nắp · Nhãn · Nhãn thùng · Thùng · Khác). Lọc chỉ ẩn
 * dòng trong bảng đó: danh sách mã đã chọn và phép tính tác động không đổi.
 */
import type { PackagingSelectedCode } from '../types/packaging-cost-types'

/** Thứ tự cố định theo vai trò trong định mức; nhóm lạ (kể cả "Khác") xếp sau, theo thứ tự xuất hiện. */
const GROUP_ORDER = ['Chai', 'Nắp', 'Nhãn', 'Nhãn thùng', 'Thùng']

export interface SelectedGroupChip {
  /** Tên nhóm đúng như `row.group`. */
  group: string
  count: number
}

/** Các nhóm CÓ mặt trong danh sách mã đã chọn, kèm số mã. Danh sách rỗng / chưa nạp → không chip nào. */
export function buildSelectedGroupChips(
  rows: readonly Pick<PackagingSelectedCode, 'group'>[] | undefined,
): SelectedGroupChip[] {
  const counts = new Map<string, number>()
  for (const row of rows ?? []) counts.set(row.group, (counts.get(row.group) ?? 0) + 1)
  const rank = (group: string) => {
    const index = GROUP_ORDER.indexOf(group)
    return index === -1 ? GROUP_ORDER.length : index
  }
  return [...counts.entries()]
    .map(([group, count]) => ({ group, count }))
    .sort((a, b) => rank(a.group) - rank(b.group))   // sort ổn định: nhóm lạ giữ thứ tự xuất hiện
}

/** `group` rỗng = Tất cả. Nhóm đã không còn trong danh sách (người dùng bỏ hết mã của nhóm) thì coi như Tất cả. */
export function resolveSelectedGroup(group: string, chips: readonly SelectedGroupChip[]): string {
  return chips.some((chip) => chip.group === group) ? group : ''
}
