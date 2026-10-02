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

//  SUBJECT_KIND / EFFECT không có gì riêng cho văn bản nên đã dọn lên
//  `shared/access-subject/subject-kind.ts` (phase 04, kế hoạch
//  `plans/261002-0836-phan-quyen-tung-bao-cao`) để phân hệ Báo cáo dùng lại
//  được. Re-export nguyên văn ở đây — KHÔNG phải barrel của module `document`
//  (luật `naming.md`: module không có barrel) — chỉ là lối tắt tương thích,
//  13 tệp cũ trong `document/` đang `import … from '../types/document-access'`
//  khỏi phải đổi theo.
export {
  SUBJECT_KIND,
  SUBJECT_KIND_LABELS,
  EFFECT,
  EFFECT_LABELS,
  type SubjectKind,
} from '@/shared/access-subject/subject-kind'

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
