import { compareSortValues, sortRowsBy } from '@/shared/utils/compare-sort-values'
import type { CategoryAssignee } from '../types/category-assignee'

/**
 * Sắp xếp phía trình duyệt cho màn Phân công phụ trách (duoc-CR-744).
 *
 * Màn này tải TRỌN danh sách một lần (`page_size=1000`) rồi lọc + phân trang tại chỗ, nên
 * xếp cũng phải làm tại chỗ và TRƯỚC khi cắt trang — xếp sau khi cắt thì chỉ đảo thứ tự
 * trong một trang. Cột `sortable` trước đây không có `onSortChange` nên tiêu đề không bấm được.
 *
 * Mỗi khóa xếp theo ĐÚNG chữ ô đang hiện (tên phân loại, tên phòng như nhãn, tên người),
 * so bằng bộ so chung `shared/utils/compare-sort-values.ts` (tiếng Việt có dấu, không phân biệt hoa thường; ô trống xuống CUỐI cả hai chiều).
 */
export type CategoryAssigneeSortKey =
  | 'item_group_name'
  | 'department_name'
  | 'primary_name'
  | 'backup_name'

export const CATEGORY_ASSIGNEE_SORT_KEYS: readonly CategoryAssigneeSortKey[] = [
  'item_group_name',
  'department_name',
  'primary_name',
  'backup_name',
]

export function isCategoryAssigneeSortKey(value: string): value is CategoryAssigneeSortKey {
  return (CATEGORY_ASSIGNEE_SORT_KEYS as readonly string[]).includes(value)
}

/** Chữ của ô theo khóa cột; chuỗi rỗng = ô đang hiện trống (dấu gạch / "Chưa phân loại"). */
function cellText(
  row: CategoryAssignee,
  key: CategoryAssigneeSortKey,
  departmentLabel: (row: CategoryAssignee) => string,
): string {
  switch (key) {
    case 'item_group_name':
      return (row.item_group_name ?? '').trim()
    case 'department_name':
      return departmentLabel(row).trim()
    case 'primary_name':
      return (row.primary_name ?? '').trim()
    case 'backup_name':
      return (row.backup_name ?? '').trim()
  }
}

/**
 * Trả BẢN SAO đã xếp; khóa lạ hoặc rỗng thì trả nguyên thứ tự gốc (backend đã xếp theo phân loại).
 * Khóa phụ: phân loại, rồi phòng, rồi id — để các dòng bằng nhau không nhảy lung tung khi tải lại.
 */
export function sortCategoryAssignees(
  rows: readonly CategoryAssignee[],
  sortBy: string,
  sortDir: 'asc' | 'desc',
  departmentLabel: (row: CategoryAssignee) => string,
): CategoryAssignee[] {
  if (!isCategoryAssigneeSortKey(sortBy)) return [...rows]
  //  Luật so (ô trống xuống cuối cả hai chiều...) nằm ở `compare-sort-values.ts`.
  return sortRowsBy(
    rows,
    (row) => cellText(row, sortBy, departmentLabel),
    sortDir,
    (a, b) =>
      compareSortValues(cellText(a, 'item_group_name', departmentLabel), cellText(b, 'item_group_name', departmentLabel)) ||
      compareSortValues(departmentLabel(a), departmentLabel(b)) ||
      a.id - b.id,
  )
}
