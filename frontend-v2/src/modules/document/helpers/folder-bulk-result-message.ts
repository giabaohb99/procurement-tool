import type { FolderLinkResult } from '../types/document-folder'

/**
 * Câu báo kết quả thao tác HÀNG LOẠT trên thư mục (thêm/chuyển/gỡ văn bản) —
 * đúng khuôn «đã {động từ} n · bị từ chối m (lý do)» ở `phase-05-...md`.
 *
 * Hàm THUẦN để test không cần dựng dialog/mutation — `folder-bulk-actions.tsx`
 * chỉ gọi nó rồi vẽ ra.
 */
export function folderBulkResultMessage(verb: string, result: FolderLinkResult): string {
  const base = `Đã ${verb} ${result.moved.length} · bị từ chối ${result.denied.length}`
  if (result.denied.length === 0) return base

  const reasons = Array.from(new Set(result.denied.map((d) => d.reason).filter(Boolean)))
  if (reasons.length === 0) return base
  if (reasons.length === 1) return `${base} (${reasons[0]})`
  return `${base} (${reasons.length} lý do khác nhau)`
}
