import type { DocumentAccess, DocumentAccessDraft } from '../types/document-access'
import { useGrantAccess, useRevokeAccess } from './use-document-access'

/**
 * Hai thao tác GHI của hộp khai quyền văn bản, dùng chung cho khối «Quyền truy
 * cập» ở trang chi tiết (`document-access-card.tsx`) và hộp «Chia sẻ» ở trang
 * Thư mục (`document-share-dialog.tsx`) — một luật, hai nơi gọi.
 */
export function useDocumentAccessEditor(documentId: number) {
  const grant = useGrantAccess(documentId)
  const revoke = useRevokeAccess(documentId)

  /** Khai mới cả lượt — văn bản đã có id nên gửi thẳng, tuần tự từng dòng. */
  async function grantAll(rows: DocumentAccessDraft[]) {
    for (const row of rows) await grant.mutateAsync(row.values)
  }

  /**
   * Sửa một dòng đã cấp. `grant` ở backend ghi đè theo (văn bản, đối tượng,
   * chiều) nên sửa = cấp lại đúng dòng đó. Nhưng đổi sang đối tượng khác (hoặc
   * đổi chiều) thì dòng vừa ghi là dòng MỚI — dòng cũ vẫn hiệu lực. Không thu
   * hồi nó thì người dùng tưởng mình vừa "sửa", thực tế là chia thêm cho một
   * người nữa mà người cũ vẫn giữ nguyên quyền.
   */
  async function saveEdit(original: DocumentAccess, rows: DocumentAccessDraft[]) {
    await grantAll(rows)
    const unchanged = rows.some(
      (row) =>
        row.values.subject_kind === original.subject_kind &&
        row.values.subject_id === original.subject_id &&
        row.values.effect === original.effect,
    )
    if (!unchanged) {
      await revoke.mutateAsync({ accessId: original.id, reason: 'Sửa lại dòng chia quyền' })
    }
  }

  /** Nạp một dòng đã cấp vào hộp khai quyền để sửa. */
  function toDraft(row: DocumentAccess): DocumentAccessDraft {
    return {
      subjectLabel: row.subject_name,
      values: {
        subject_kind: row.subject_kind,
        subject_id: row.subject_id,
        effect: row.effect,
        can_read: true,
        can_write: row.can_write,
        can_delete: row.can_delete,
        valid_from: row.valid_from,
        valid_to: row.valid_to,
        reason: row.reason,
      },
    }
  }

  return { grant, revoke, grantAll, saveEdit, toDraft, pending: grant.isPending || revoke.isPending }
}
