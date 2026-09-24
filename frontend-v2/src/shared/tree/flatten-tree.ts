import type { FlatTreeNode, TreeNode } from './tree-types'

/**
 * Trải cây thành DANH SÁCH PHẲNG theo thứ tự hiện trên màn hình (duyệt trước —
 * cha rồi mới tới con), CHỈ giữ những node đang THẤY được: nhánh gập thì con
 * của nó không xuất hiện trong kết quả.
 *
 * Dùng cho điều hướng bàn phím (↑↓ nhảy giữa các dòng ĐANG HIỆN, không nhảy
 * vào nhánh đang gập) và cho vẽ bảng ảo sau này nếu cây quá dài.
 *
 * Hàm THUẦN — không tự giữ state gập/mở, nhận `isExpanded` từ ngoài
 * (`useTreeExpansion`) để gọi lại được với bất kỳ nguồn trạng thái nào.
 */
export function flattenTree<T>(
  nodes: TreeNode<T>[],
  isExpanded: (id: string | number) => boolean,
  depth = 0,
  parentId: string | number | null = null,
): FlatTreeNode<T>[] {
  const out: FlatTreeNode<T>[] = []
  for (const node of nodes) {
    //  `expandable` ÉP hiện chevron dù chưa có `children` thật (thư mục biết
    //  chắc có thể có con nhưng chưa nạp/đang trống) — xem `tree-types.ts`.
    const hasChildren = Boolean(node.children && node.children.length > 0) || node.expandable === true
    out.push({ id: node.id, label: node.label, depth, parentId, hasChildren, data: node.data })
    if (hasChildren && isExpanded(node.id)) {
      //  `node.children ?? []`: node ÉP `expandable` mà chưa có `children` thật
      //  (chưa nạp xong) vẫn phải trải phẳng an toàn, không rơi vào
      //  `flattenTree(undefined, …)`.
      out.push(...flattenTree(node.children ?? [], isExpanded, depth + 1, node.id))
    }
  }
  return out
}
