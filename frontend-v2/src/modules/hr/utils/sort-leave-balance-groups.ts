import { sortRowsBy, type SortDir, type SortValue } from '@/shared/utils/compare-sort-values'
import {
  policyNameOfRow,
  type LeaveBalanceGroup,
  type LeaveBalanceTotals,
} from './group-leave-balances'

/**
 * XẾP CÁC NHÓM NGƯỜI của bảng Quỹ phép năm, thẻ *Theo dòng quỹ* (duoc-CR-748).
 *
 * Bảng nạp TRỌN quỹ của năm rồi gom theo người và cắt trang ở trình duyệt (`leave-balance-rows-table.tsx`), nên
 * xếp cũng ở trình duyệt — nhưng xếp NHÓM chứ không xếp dòng quỹ, và phải xếp TRƯỚC khi cắt trang: xếp dòng quỹ thì
 * một người tám loại nghỉ bị xé ra tám chỗ, mất đúng con số tổng mà hàng người bày ra. Dòng con trong mỗi nhóm giữ
 * nguyên thứ tự loại nghỉ backend trả về.
 *
 * Mỗi cột xếp theo đúng giá trị hàng NGƯỜI đang hiện:
 * - Nhân sự: tên (có dấu, không phân biệt hoa thường); tên rỗng thì nhóm hiện `#<id>` và xếp theo đúng chữ đó.
 * - Chính sách: tên các gói gộp lại như ô đang hiện; không gói nào (ô hiện chữ mờ *Theo loại nghỉ*) là ô trống.
 * - Cột số: tổng của nhóm. Ô hiện dấu gạch khi bằng 0 (`DayCount`), nên số 0 là ô trống và xuống CUỐI ở cả hai
 *   chiều — trừ cột *Còn lại*: ô đó luôn in số, 0 ở đây nghĩa là *hết phép*, là giá trị thật phải xếp như số.
 *
 * Bằng nhau thì tên người tăng dần rồi id nhân sự — thứ tự không đổi giữa các lần dựng, không ai nhảy trang.
 */

/** Cột số của bảng — khóa cột trùng tên trường tổng. */
const DAY_COLUMNS = new Set<string>([
  'allocated_days',
  'seniority_days',
  'carried_days',
  'adjusted_days',
  'comp_days',
  'encashed_days',
  'carried_out_days',
  'carried_expired_days',
  'used_days',
  'pending_days',
  'total_days',
  'remaining_days',
] satisfies (keyof LeaveBalanceTotals)[])

/** Cột số LUÔN in số (kể cả 0) — xem `alwaysShow` ở cột *Còn lại* của `leave-balance-columns.tsx`. */
const ALWAYS_SHOWN_DAY_COLUMNS = new Set<string>(['remaining_days'])

/** Giá trị đem so của một nhóm ở cột `columnKey` (đã biết là cột xếp được). */
function groupSortValue(group: LeaveBalanceGroup, columnKey: string): SortValue {
  if (columnKey === 'employee_name') return group.employeeName
  //  Cùng hàm dựng chữ của ô Chính sách ở hàng người — xếp theo đúng chữ đang hiện.
  if (columnKey === 'policy_name') return policyNameOfRow({ kind: 'group', id: '', group })
  const value = group.totals[columnKey as keyof LeaveBalanceTotals]
  if (ALWAYS_SHOWN_DAY_COLUMNS.has(columnKey)) return value
  return value === 0 ? null : value
}

const nameCollator = new Intl.Collator('vi', { numeric: true, sensitivity: 'base' })

function byNameThenId(a: LeaveBalanceGroup, b: LeaveBalanceGroup): number {
  return nameCollator.compare(a.employeeName, b.employeeName) || a.employeeId - b.employeeId
}

/** Các khóa cột xếp được — để bảng bật `sortable` đúng những cột này. */
export const LEAVE_BALANCE_SORTABLE_KEYS: ReadonlySet<string> = new Set([
  'employee_name',
  'policy_name',
  ...DAY_COLUMNS,
])

/**
 * Trả BẢN SAO các nhóm đã xếp. Khóa rỗng (nhịp thứ ba của tiêu đề = thôi sắp xếp) hoặc khóa lạ thì giữ nguyên
 * thứ tự gốc của backend.
 */
export function sortLeaveBalanceGroups(
  groups: readonly LeaveBalanceGroup[],
  sortBy: string,
  sortDir: SortDir,
): LeaveBalanceGroup[] {
  if (!sortBy || !LEAVE_BALANCE_SORTABLE_KEYS.has(sortBy)) return [...groups]
  return sortRowsBy(groups, (group) => groupSortValue(group, sortBy), sortDir, byNameThenId)
}
