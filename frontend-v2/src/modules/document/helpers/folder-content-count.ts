import type { DocFolderTreeNode } from '../types/document-folder'

/**
 * Đếm THƯ MỤC CON TRỰC TIẾP của từng thư mục từ danh sách phẳng `/tree`
 * (theo `parent_id`). `/tree` chỉ trả thư mục người xem THẤY được, nên số
 * đếm cũng chỉ tính những thư mục đó — khớp đúng thứ họ mở ra sẽ thấy.
 */
export function countSubfoldersByParent(
  rows: readonly DocFolderTreeNode[] | undefined,
): Map<number, number> {
  const counts = new Map<number, number>()
  for (const row of rows ?? []) {
    if (row.parent_id <= 0) continue
    counts.set(row.parent_id, (counts.get(row.parent_id) ?? 0) + 1)
  }
  return counts
}

/**
 * Dòng phụ trên thẻ thư mục (chốt 24/09/2026, kiểu thẻ Google Drive + số
 * lượng): «2 thư mục · 5 văn bản», bỏ vế nào bằng 0, cả hai bằng 0 → «Trống».
 * Số văn bản là `document_count_branch` — đếm CẢ NHÁNH, đã khử trùng.
 */
export function formatFolderContentCount(subfolderCount: number, documentCount: number): string {
  const parts: string[] = []
  if (subfolderCount > 0) parts.push(`${subfolderCount} thư mục`)
  if (documentCount > 0) parts.push(`${documentCount} văn bản`)
  return parts.length > 0 ? parts.join(' · ') : 'Trống'
}
