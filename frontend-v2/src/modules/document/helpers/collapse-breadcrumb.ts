import type { FolderBreadcrumbItem } from '../types/document-folder'

/** Đường dẫn DÀI thì mới gập — bằng hoặc ngắn hơn ngưỡng này thì hiện đủ. */
const MAX_VISIBLE = 4

export interface CollapsedBreadcrumb {
  /** Đoạn ĐẦU hiện nguyên (gốc pháp nhân) — rỗng khi không cần gập. */
  head: FolderBreadcrumbItem[]
  /** Đoạn GIỮA bị gập vào menu «…» — rỗng khi không cần gập. */
  collapsed: FolderBreadcrumbItem[]
  /** Đoạn CUỐI hiện nguyên, LUÔN gồm ít nhất chính thư mục đang xem. */
  tail: FolderBreadcrumbItem[]
}

/**
 * Quyết định đoạn nào hiện/gập của breadcrumb khung nội dung (đặc tả §4,
 * duoc-CR-476: "long paths collapse middle segments into «…» dropdown") — hàm
 * THUẦN, tách khỏi `folder-breadcrumb.tsx` để test không cần dựng DOM.
 *
 * Đường ngắn (≤ {@link MAX_VISIBLE} đoạn) hiện NGUYÊN VẸN, không gập gì cả.
 * Đường dài giữ lại: gốc pháp nhân (đầu) + cha trực tiếp và chính nó (cuối) —
 * hai đầu mút là chỗ người dùng cần bấm nhất (về gốc / lên một cấp), phần giữa
 * gập vào «…».
 */
export function collapseBreadcrumb(
  crumbs: readonly FolderBreadcrumbItem[],
): CollapsedBreadcrumb {
  if (crumbs.length <= MAX_VISIBLE) return { head: [], collapsed: [], tail: [...crumbs] }
  return {
    head: [crumbs[0]],
    collapsed: crumbs.slice(1, crumbs.length - 2),
    tail: crumbs.slice(crumbs.length - 2),
  }
}
