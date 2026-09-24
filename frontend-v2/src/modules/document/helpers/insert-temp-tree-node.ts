import type { TreeNode } from '@/shared/tree/tree-types'

/** id CỦA dòng tạm «thư mục mới» — kiểu VS Code Explorer, không có bản ghi thật đứng sau nó. */
export const NEW_FOLDER_TEMP_ID = '__new_folder__'

/** `parent_id` của thư mục ở GỐC cây (pháp nhân + thư mục tự do). */
export const ROOT_PARENT_ID = 0

/**
 * Chèn một node TẠM (chưa có bản ghi thật, `data` luôn `undefined`) làm con
 * ĐẦU TIÊN của `parentId` — dùng cho dòng nhập «thư mục mới» kiểu VS Code (gõ
 * tên ngay trong cây, không mở hộp thoại; xem `folder-tree-panel.tsx`).
 *
 * Hàm THUẦN, trả về CÂY MỚI (không sửa `nodes` gốc) — `parentId` không có
 * trong cây (đã bị lọc bởi ô tìm thư mục, ví dụ) thì trả nguyên cây cũ, không
 * nổ và không âm thầm chèn nhầm chỗ.
 */
export function insertTempChildNode<T>(
  nodes: TreeNode<T>[],
  parentId: string | number,
): TreeNode<T>[] {
  //  `label` rỗng vì `folder-tree-panel.tsx` LUÔN thay dòng này bằng ô nhập
  //  (`renderLabel`) — không bao giờ vẽ nhãn tĩnh của node tạm.
  const tempNode: TreeNode<T> = { id: NEW_FOLDER_TEMP_ID, label: '' }

  //  `parentId = ROOT_PARENT_ID` (0) = tạo THƯ MỤC TỰ DO ở gốc cây (mở
  //  24/09/2026) — dòng nhập nằm ĐẦU danh sách gốc, không lồng vào nút nào.
  if (parentId === ROOT_PARENT_ID) return [tempNode, ...nodes]

  function walk(list: TreeNode<T>[]): TreeNode<T>[] {
    return list.map((node) => {
      if (node.id === parentId) {
        return { ...node, children: [tempNode, ...(node.children ?? [])] }
      }
      if (node.children?.length) {
        return { ...node, children: walk(node.children) }
      }
      return node
    })
  }

  return walk(nodes)
}
