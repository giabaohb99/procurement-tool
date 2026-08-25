/**
 * QUYỀN TRÊN TỪNG VĂN BẢN — ai được thấy, đọc, sửa, xóa văn bản cụ thể này.
 *
 * Lớp thứ ba, đứng cạnh hai lớp đã có chứ không thay thế lớp nào:
 *  1. vai trò (`can('document', ...)`) — được đụng vào loại việc này không;
 *  2. phạm vi dữ liệu — trong đó thì thấy nhóm văn bản nào;
 *  3. **bảng này** — riêng văn bản này mở thêm / khóa bớt cho ai.
 *
 * Hai điều nhìn trên giao diện sẽ thấy ngay, ghi ở đây cho khỏi phải đoán:
 *  - **CẤM thắng CHO PHÉP** và thắng cả phạm vi vai trò;
 *  - **thu hồi là đánh dấu, không xóa dòng** — bảng vẫn hiện dòng đã thu hồi
 *    kèm mốc và lý do, vì câu người ta hỏi khi có chuyện là "hồi tháng 7 ai
 *    đọc được văn bản này".
 */

export const SUBJECT_KIND = {
  employee: 1,
  department: 2,
  company: 3,
  role: 4,
} as const

export type SubjectKind = (typeof SUBJECT_KIND)[keyof typeof SUBJECT_KIND]

export const SUBJECT_KIND_LABELS: Record<number, string> = {
  1: 'Người',
  2: 'Phòng ban',
  3: 'Pháp nhân',
  4: 'Vai trò',
}

export const EFFECT = { allow: 1, deny: 2 } as const

export const EFFECT_LABELS: Record<number, string> = {
  1: 'Cho phép',
  2: 'Không cho phép',
}

export interface DocumentAccess {
  id: number
  document_id: number
  subject_kind: number
  subject_kind_label: string
  subject_id: number
  subject_name: string
  /** 1 cho phép · 2 cấm. */
  effect: number
  effect_label: string
  /** "Thấy" và "đọc" là một: không cho đọc thì cũng không hiện trong danh sách. */
  can_read: boolean
  can_write: boolean
  can_delete: boolean
  valid_from: string | null
  /** Trống = không hạn. */
  valid_to: string | null
  reason: string
  /** Còn hiệu lực (chưa thu hồi). Dòng đã thu hồi vẫn nằm trong danh sách. */
  is_active: boolean
  revoked_at: string
  revoked_by_name: string
  revoke_reason: string
  granted_by_name: string
  created_at: string
}

export interface DocumentAccessInput {
  subject_kind: number
  subject_id: number
  effect: number
  can_read: boolean
  can_write: boolean
  can_delete: boolean
  valid_from: string | null
  valid_to: string | null
  reason: string
}

/**
 * Một dòng quyền vừa khai trong hộp chia quyền, CHƯA gửi lên máy chủ.
 *
 * `subjectLabel` đi kèm để nơi nhận hiện tên đối tượng mà không phải tra lại
 * danh mục — trang tạo văn bản xếp hàng chờ tới lúc có id văn bản mới gửi.
 */
export interface DocumentAccessDraft {
  values: DocumentAccessInput
  subjectLabel: string
}
