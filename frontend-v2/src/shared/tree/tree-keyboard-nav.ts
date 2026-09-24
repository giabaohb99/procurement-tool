import type { FlatTreeNode } from './tree-types'

export type TreeKeyAction<T> =
  | { type: 'focus'; id: string | number }
  | { type: 'toggle'; id: string | number }
  | { type: 'select'; row: FlatTreeNode<T> }

/**
 * Quy tắc điều hướng bàn phím của `TreeView` (roving tabindex, mẫu APG
 * «treeview») — tách thành hàm THUẦN để test không cần dựng DOM/React. Trả
 * `null` cho phím không xử lý (nơi gọi tự bỏ qua, không gọi `preventDefault`).
 */
export function resolveTreeKeyAction<T>(
  key: string,
  flat: FlatTreeNode<T>[],
  index: number,
  expandedIds: ReadonlySet<string | number>,
): TreeKeyAction<T> | null {
  const row = flat[index]
  if (!row) return null

  switch (key) {
    case 'ArrowDown': {
      const next = flat[index + 1]
      return next ? { type: 'focus', id: next.id } : null
    }
    case 'ArrowUp': {
      const prev = flat[index - 1]
      return prev ? { type: 'focus', id: prev.id } : null
    }
    case 'ArrowRight': {
      if (row.hasChildren && !expandedIds.has(row.id)) return { type: 'toggle', id: row.id }
      const next = flat[index + 1]
      return next ? { type: 'focus', id: next.id } : null
    }
    case 'ArrowLeft': {
      if (row.hasChildren && expandedIds.has(row.id)) return { type: 'toggle', id: row.id }
      return row.parentId !== null ? { type: 'focus', id: row.parentId } : null
    }
    case 'Home': {
      const first = flat[0]
      return first ? { type: 'focus', id: first.id } : null
    }
    case 'End': {
      const last = flat[flat.length - 1]
      return last ? { type: 'focus', id: last.id } : null
    }
    case 'Enter':
    case ' ':
      return { type: 'select', row }
    default:
      return null
  }
}
