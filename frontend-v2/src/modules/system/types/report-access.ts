/**
 * PHÂN QUYỀN TỪNG BÁO CÁO — tab «Báo cáo» của màn Phân quyền tài khoản.
 *
 * Gác KÉP với quyền phân hệ gốc (xem `backend/app/core/report_keys.py` +
 * `app/modules/report_access/`, phase 01-02 của kế hoạch
 * `plans/261002-0836-phan-quyen-tung-bao-cao`): một tài khoản phải có CẢ
 * `can('report', 'read')` (hoặc quyền phân hệ tương ứng) LẪN một dòng CHO
 * PHÉP ở đây mới xem được báo cáo — gán ở đây chỉ MỞ báo cáo, không mở rộng
 * phạm vi dữ liệu nhìn thấy bên trong nó.
 *
 * Bốn loại chủ thể + chiều tác động dùng CHUNG `@/shared/access-subject` —
 * không khai `SUBJECT_KIND`/`EFFECT` riêng ở đây.
 */

/** Một dòng CÒN SỐNG (chưa thu hồi) — `GET /api/report-access` chỉ trả loại này. */
export interface ReportAccessGrant {
  id: number
  subject_kind: number
  subject_kind_label: string
  subject_id: number
  subject_name: string
  /** 1 cho phép · 2 cấm (`EFFECT` ở `@/shared/access-subject/subject-kind`). */
  effect: number
  reason: string
  valid_from: string | null
  valid_to: string | null
  created_at: string
}

/** Một trong 13 báo cáo (`ReportKey` phía backend), kèm mọi dòng đang gán. */
export interface ReportAccessItem {
  key: number
  label: string
  /** Tên nhóm phân hệ do BACKEND trả — không gõ tay, không import danh mục của `modules/report`. */
  group: string
  grants: ReportAccessGrant[]
}

/** Thân `POST /api/report-access/{key}/grants`. */
export interface GrantReportAccessInput {
  subjects: { subject_kind: number; subject_id: number }[]
  effect: number
  reason?: string
  valid_from?: string | null
  valid_to?: string | null
}

/** Một chủ thể backend không gán được (không tìm thấy) — vẫn gán phần còn lại, báo riêng phần này. */
export interface SkippedSubject {
  subject_kind: number
  subject_id: number
  reason: string
}

/** Kết quả `POST .../grants` — có thể gán một phần, bỏ qua phần còn lại. */
export interface GrantReportAccessResult {
  created: number
  updated: number
  skipped: SkippedSubject[]
}
