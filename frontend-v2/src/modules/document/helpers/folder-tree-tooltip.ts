import type { DocFolderTreeNode } from '../types/document-folder'

/**
 * Chữ tooltip đầy đủ của một nút cây thư mục — TÊN PHÁP LÝ ĐẦY ĐỦ (không rút
 * gọn như `display_name`) nối theo ĐƯỜNG DẪN từ gốc, cách nhau " / ". Dùng khi
 * tên hiển thị đã rút gọn (gốc pháp nhân dùng `short_name`) hoặc bị cắt bởi bề
 * ngang khung 200–480px (yêu cầu giao diện kiểu VS Code, 23/09/2026).
 *
 * Hàm THUẦN, đi bằng `parent_id` qua map `byId` — không đọc `path` (chuỗi id
 * vật hóa `/1/5/9/`) vì cần TÊN từng cấp chứ không phải id. Chặn vòng lặp dữ
 * liệu hỏng bằng `seen` giống `build-folder-tree.ts::isAncestor`.
 */
export function buildFolderTooltip(
  node: Pick<DocFolderTreeNode, 'id' | 'name' | 'parent_id'>,
  byId: ReadonlyMap<number, Pick<DocFolderTreeNode, 'id' | 'name' | 'parent_id'>>,
): string {
  const chain: string[] = []
  const seen = new Set<number>()
  let cursor: Pick<DocFolderTreeNode, 'id' | 'name' | 'parent_id'> | undefined = node
  while (cursor && !seen.has(cursor.id)) {
    seen.add(cursor.id)
    chain.unshift(cursor.name)
    cursor = cursor.parent_id && cursor.parent_id !== cursor.id ? byId.get(cursor.parent_id) : undefined
  }
  return chain.join(' / ')
}
