import type { TreeNode } from './tree-types'

export interface FilterTreeResult<T> {
  /** Cây đã lọc — chỉ còn nhánh có ít nhất một node khớp (bản thân hoặc con cháu). */
  nodes: TreeNode<T>[]
  /**
   * id của các node THẬT SỰ khớp `predicate` — khác với node chỉ còn lại vì nó
   * là TỔ TIÊN của một kết quả. `TreeView` dùng tập này để tô sáng đúng dòng
   * khớp, không tô nhầm cả đường dẫn dẫn tới nó.
   */
  matchedIds: Set<string | number>
}

/**
 * Lọc cây theo `predicate`, GIỮ LẠI tổ tiên của mọi node khớp dù bản thân tổ
 * tiên không khớp gì cả — thiếu bước này thì lọc theo tên là cây rời rạc từng
 * mẩu, người xem không biết kết quả nằm ở thư mục nào.
 *
 * Node KHÔNG có con (leaf) và không khớp thì bị loại hẳn, không phải ẩn bằng
 * CSS — trả về đúng tập cây con để `TreeView` không phải tự lọc lại.
 */
export function filterTree<T>(
  nodes: TreeNode<T>[],
  predicate: (node: TreeNode<T>) => boolean,
): FilterTreeResult<T> {
  const matchedIds = new Set<string | number>()

  function walk(list: TreeNode<T>[]): TreeNode<T>[] {
    const out: TreeNode<T>[] = []
    for (const node of list) {
      const selfMatch = predicate(node)
      const filteredChildren = node.children ? walk(node.children) : undefined
      const childMatched = Boolean(filteredChildren && filteredChildren.length > 0)
      if (selfMatch) matchedIds.add(node.id)
      if (selfMatch || childMatched) {
        out.push(filteredChildren ? { ...node, children: filteredChildren } : node)
      }
    }
    return out
  }

  return { nodes: walk(nodes), matchedIds }
}
