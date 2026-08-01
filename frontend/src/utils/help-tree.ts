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
