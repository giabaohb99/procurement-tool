import type { TreeNode } from '@/shared/tree/tree-types'
import type { DocFolderTreeNode } from '../types/document-folder'

/**
 * Dựng cây lồng nhau từ danh sách PHẲNG mà `GET /api/doc-folders/tree` trả về.
 *
 * - Anh em sắp theo `sort_order` rồi theo tên (so theo tiếng Việt) — backend
 *   không hứa thứ tự của danh sách phẳng.
 * - Nút có `parent_id` trỏ tới thư mục KHÔNG có trong danh sách (người xem không
 *   thấy cha) được đưa lên làm gốc, chứ không bị rơi mất: rơi mất là người dùng
 *   có quyền với thư mục đó mà không bao giờ thấy nó trên cây.
 * - Vòng lặp dữ liệu (không nên có — backend chặn) không làm treo: mỗi id chỉ
 *   được gắn đúng một lần.
 */
export function buildFolderTree(
  rows: readonly DocFolderTreeNode[],
): TreeNode<DocFolderTreeNode>[] {
  const nodes = new Map<number, TreeNode<DocFolderTreeNode>>()
  for (const row of rows) {
    if (!nodes.has(row.id)) {
      nodes.set(row.id, {
        id: row.id,
        //  `display_name` (tên gọi tắt — gốc pháp nhân ưu tiên `short_name`,
        //  yêu cầu 23/09/2026) — rơi về `name` khi backend cũ/test chưa khai
        //  trường này (field tùy chọn, xem `document-folder.ts`).
        label: row.display_name || row.name,
        data: row,
        children: [],
        //  MỌI thư mục đều có thể mở ra xem văn bản trực tiếp bên trong (kể
        //  cả khi chưa có thư mục con) — chevron luôn hiện, kiểu VS Code
        //  Explorer, xem `insert-folder-document-leaves.ts`.
        expandable: true,
      })
    }
  }

  const roots: TreeNode<DocFolderTreeNode>[] = []
  for (const node of nodes.values()) {
    const parentId = node.data?.parent_id ?? 0
    const parent = parentId !== node.id ? nodes.get(parentId) : undefined
    if (parent && !isAncestor(node, parent, nodes)) {
      parent.children?.push(node)
    } else {
      roots.push(node)
    }
  }

  sortRecursively(roots)
  return roots
}

/** `candidate` có phải con cháu của `node` không — chặn gắn tạo vòng. */
function isAncestor(
  node: TreeNode<DocFolderTreeNode>,
  candidate: TreeNode<DocFolderTreeNode>,
  nodes: Map<number, TreeNode<DocFolderTreeNode>>,
): boolean {
  const seen = new Set<number>()
  let cursor: TreeNode<DocFolderTreeNode> | undefined = candidate
  while (cursor?.data && !seen.has(cursor.data.id)) {
    if (cursor.data.id === node.id) return true
    seen.add(cursor.data.id)
    const nextId: number = cursor.data.parent_id
    cursor = nextId !== cursor.data.id ? nodes.get(nextId) : undefined
  }
  return false
}

function compareSiblings(a: TreeNode<DocFolderTreeNode>, b: TreeNode<DocFolderTreeNode>): number {
  const byOrder = (a.data?.sort_order ?? 0) - (b.data?.sort_order ?? 0)
  return byOrder !== 0 ? byOrder : a.label.localeCompare(b.label, 'vi')
}

function sortRecursively(list: TreeNode<DocFolderTreeNode>[]): void {
  list.sort(compareSiblings)
  for (const node of list) {
    if (node.children?.length) sortRecursively(node.children)
    else delete node.children
  }
}
