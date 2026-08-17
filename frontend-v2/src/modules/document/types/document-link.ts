/**
 * QUAN HỆ CHA–CON giữa các văn bản (nhóm E) và BẢN TRÍCH NỘI BỘ (C19).
 *
 * Mười giá trị `relation` khai cứng ở backend (`link_rule_model.py`); ở đây chỉ
 * giữ hai giá trị mà giao diện phải tự biết:
 *  - `EXCERPT` để nhận ra dòng trích từ (khóa, không gỡ được);
 *  - `REFERENCE` là liên kết mềm, khai được với loại nào cũng được.
 *
 * Nhãn tiếng Việt KHÔNG chép ở đây — backend trả kèm `relation_label`, và câu
 * đọc ngược (`Được hướng dẫn bởi`) chỉ backend mới dựng đúng theo phía đang xem.
 */

export const RELATION = {
  replace: 1,
  amend: 2,
  supplement: 3,
  guide: 4,
  attached: 5,
  belongs: 6,
  basedOn: 7,
  reference: 8,
  revoke: 9,
  /** Trích từ — chỉ sinh ra khi tạo bản trích, không khai tay được. */
  excerpt: 10,
} as const

/** Tóm tắt một dòng của văn bản đầu kia — vừa đủ nhìn ra là văn bản gì. */
export interface LinkedDocument {
  id: number
  title: string
  display_code: string
  doc_type_id: number | null
  status: number
  status_label: string
  secrecy_level: number
  version_no: string
  needs_review: boolean
}

export interface DocumentLink {
  id: number
  relation: number
  /** Câu đã đọc ĐÚNG THEO phía đang xem — không tự ghép ở giao diện. */
  relation_label: string
  /** `outgoing` = văn bản đang mở là nguồn; chỉ chiều này mới gỡ được. */
  direction: 'outgoing' | 'incoming'
  document: LinkedDocument | null
  note: string
  /** Hệ thống tạo (trích từ, clone) — không có nút gỡ. */
  is_system: boolean
  source_version_id: number | null
  /** Bản trích đang bám theo một phiên bản cũ của gốc. */
  is_outdated: boolean
}

export interface DocumentLinkList {
  outgoing: DocumentLink[]
  incoming: DocumentLink[]
  /** E04 — còn thiếu gì thì chưa gửi duyệt được. Rỗng nghĩa là đủ. */
  missing_required: string[]
}

/** Một ô quan hệ mà form phải tự hiện theo loại văn bản (E03). */
export interface DocumentLinkSlot {
  rule_id: number
  relation: number
  relation_label: string
  target_type_id: number | null
  /** Tên loại đích, hoặc "Loại bất kỳ". Hai ô cùng quan hệ phân biệt nhau bằng đây. */
  target_type_name: string
  is_required: boolean
  min_count: number
  /** 0 = không giới hạn. */
  max_count: number
  /** Đã lọc sẵn đúng loại đích cho phép và chỉ văn bản còn hiệu lực. */
  options: LinkedDocument[]
}

/** Một nút trên cây tài liệu (E06). */
export interface DocumentTreeNode extends LinkedDocument {
  relation?: number
  relation_label?: string
  is_outdated?: boolean
  children: DocumentTreeNode[]
}

/**
 * J10 — một văn bản đang sửa đổi / thay thế / bãi bỏ văn bản đang mở.
 *
 * Chỉ gồm văn bản ĐÃ BAN HÀNH: dự thảo sửa đổi còn trong ngăn kéo thì chưa đổi
 * gì cả, gắn nhãn sớm là dọa người đọc bằng một thứ chưa có hiệu lực.
 */
export interface DocumentAmendment {
  document_id: number
  title: string
  display_code: string
  relation: number
  relation_label: string
  effective_date: string | null
  status_label: string
}

/** Một văn bản sẽ đổi trạng thái khi văn bản đang mở được ban hành (J10). */
export interface SupersedeTarget {
  document_id: number
  title: string
  display_code: string
  relation_label: string
  current_status_label: string
  next_status_label: string
}

/**
 * J04 — mọi thứ sắp xảy ra khi bấm Ban hành.
 *
 * `blockers` là thứ backend SẼ TỪ CHỐI; `warnings` là thứ vẫn ban hành được
 * nhưng gần như chắc chắn là quên. Gộp chung hai loại thì người dùng học được
 * thói quen bỏ qua tất.
 */
export interface DocumentIssuePreview {
  version_id: number | null
  version_no: string
  effective_date: string | null
  /** Có hiệu lực ngay hay còn chờ tới ngày — quyết định văn bản cũ chết ngay hay chưa. */
  effective_now: boolean
  issue_number_preview: string
  number_on_approve: boolean
  needs_decision: boolean
  has_decision: boolean
  scope_count: number
  will_supersede: SupersedeTarget[]
  blockers: string[]
  warnings: string[]
}

export interface DocumentLinkInput {
  relation: number
  target_document_id: number
  note?: string
}

export interface DocumentExcerptInput {
  title: string
  content_html: string
  secrecy_level: number
  note?: string
}
