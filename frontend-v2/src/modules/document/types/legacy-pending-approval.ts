/**
 * Một văn bản chờ DUYỆT MỘT BƯỚC — `GET /api/document-approvals/legacy-pending`.
 *
 * Không có việc (task) trong bộ máy duyệt, nên không có hạn, không có bước,
 * không có ủy quyền: người có quyền duyệt và đọc được văn bản là duyệt được.
 */
export interface LegacyPendingDocument {
  document_id: number
  code: string
  title: string
  version_label: string
  submitted_by_name: string
  submitted_at: string | null
}

/**
 * Một lượt TÔI đã bấm theo đường duyệt một bước — `GET
 * /api/document-approvals/legacy-decisions`. Đọc từ nhật ký văn bản vì sổ
 * của bộ máy duyệt không có dòng nào cho đường này.
 */
export interface LegacyDecision {
  /** Id dòng nhật ký — một văn bản trả về rồi duyệt lại ra hai dòng. */
  id: number
  document_id: number
  code: string
  title: string
  /** Cùng mã với bộ máy duyệt: 2 Duyệt · 4 Trả lại. */
  action: number
  action_label: string
  comment: string
  decided_at: string
  /** Trạng thái HIỆN TẠI của văn bản. */
  status_label: string
}
