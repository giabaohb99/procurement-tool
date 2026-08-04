// Tiện ích dựng cây & tìm đường dẫn breadcrumb cho Trung tâm Hướng dẫn sử dụng (HDSD).
// API trả danh sách phẳng (id, parent_id) — client tự dựng cây.

export interface HelpNode {
  id: number
  parent_id: number | null
  title: string
  sort_order: number
  children?: HelpNode[]
}

export interface HelpCrumb {
  id: number
  title: string
}

/** Dựng cây từ danh sách phẳng. Node có parent_id trỏ tới id không tồn tại được coi là node gốc. */
export function buildTree(nodes: HelpNode[]): HelpNode[] {
  const nodeMap = new Map<number, HelpNode>()
  nodes.forEach((n) => nodeMap.set(n.id, { ...n, children: [] }))

  const tree: HelpNode[] = []
  nodeMap.forEach((n) => {
    const parent = n.parent_id !== null ? nodeMap.get(n.parent_id) : undefined
    if (parent) parent.children!.push(n)
    else tree.push(n)
  })
  return tree
}

/** Tìm 1 node theo id trong cây. null nếu không có. */
export function findNode(tree: HelpNode[], targetId: number): HelpNode | null {
  for (const node of tree) {
    if (node.id === targetId) return node
    const found = node.children?.length ? findNode(node.children, targetId) : null
    if (found) return found
  }
  return null
}

/** Node cha của targetId. null nếu targetId là node gốc hoặc không tồn tại. */
export function findParent(tree: HelpNode[], targetId: number): HelpNode | null {
  for (const node of tree) {
    if (node.children?.some((c) => c.id === targetId)) return node
    const found = node.children?.length ? findParent(node.children, targetId) : null
    if (found) return found
  }
  return null
}

/** Đường dẫn từ gốc tới node targetId (dùng cho breadcrumb). null nếu không tìm thấy. */
export function findPath(
  tree: HelpNode[],
  targetId: number,
  currentPath: HelpCrumb[] = [],
): HelpCrumb[] | null {
  for (const node of tree) {
    const path = [...currentPath, { id: node.id, title: node.title }]
    if (node.id === targetId) return path
    if (node.children?.length) {
      const found = findPath(node.children, targetId, path)
      if (found) return found
    }
  }
  return null
}

/** Tổng số bài viết trong 1 nhánh (không tính chính node). */
export function countDescendants(node: HelpNode): number {
  return (node.children || []).reduce((sum, c) => sum + 1 + countDescendants(c), 0)
}

/** Chiều cao nhánh tính từ node (0 = node lá, 1 = có con, 2 = có cháu). */
export function articleHeight(node: HelpNode): number {
  const children = node.children || []
  return children.length === 0 ? 0 : 1 + Math.max(...children.map(articleHeight))
}

/** Duỗi cây thành danh sách phẳng kèm độ sâu — dùng cho ô chọn thư mục cha. */
export function flattenTree(nodes: HelpNode[], depth = 0): { node: HelpNode; depth: number }[] {
  return nodes.flatMap((node) => [
    { node, depth },
    ...flattenTree(node.children || [], depth + 1),
  ])
}
