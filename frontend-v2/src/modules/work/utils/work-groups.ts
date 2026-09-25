import type { WorkGroup, WorkGroupNode, WorkSidebar } from '../types/work'

/** Một nhóm đã DUỖI PHẲNG từ cây, kèm độ sâu để thụt lề trong ô chọn. */
export interface FlatWorkGroup extends WorkGroup {
  depth: number
  /** Số dự án nằm TRỰC TIẾP trong nhóm (không đếm nhóm con). */
  listCount: number
}

/**
 * Duỗi cây nhóm → danh sách phẳng theo thứ tự cây (cha rồi tới con) — bao-CR-482.
 *
 * Ô chọn «Nhóm» của dự án và cụm nhóm ở màn liệt kê đều cần một danh sách phẳng;
 * cây chỉ có hai cấp (backend chặn cấp 3) nhưng viết đệ quy cho khỏi lệ thuộc.
 */
export function flattenGroups(sidebar: WorkSidebar | undefined): FlatWorkGroup[] {
  const out: FlatWorkGroup[] = []
  const walk = (nodes: WorkGroupNode[], depth: number) => {
    for (const node of nodes) {
      const { lists, children, ...group } = node
      out.push({ ...group, depth, listCount: lists.length })
      walk(children, depth + 1)
    }
  }
  walk(sidebar?.groups ?? [], 0)
  return out
}

/** Tên nhóm theo id — cho cột «Nhóm» của bảng dự án. Không có = đứng ngoài nhóm. */
export function groupNameOf(groups: FlatWorkGroup[], groupId: number | null): string {
  if (!groupId) return ''
  return groups.find((g) => g.id === groupId)?.name ?? `Nhóm #${groupId}`
}

/** Nhãn cho dự án không thuộc nhóm nào — một chữ, dùng chung mọi chỗ. */
export const NO_GROUP_LABEL = 'Ngoài nhóm'
