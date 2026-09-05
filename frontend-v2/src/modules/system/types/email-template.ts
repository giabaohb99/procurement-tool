/** Mẫu email thông báo theo bước (event) — đọc từ /api/email-templates. */
export interface EmailTemplate {
  event: string
  /** Tên bước (vd "Duyệt", "Hoàn tất"). */
  label: string
  /** Nhóm người nhận email này (vd "Điều phối viên", "Người tạo"). */
  recipient: string
  enabled: boolean
  subject: string
  body_html: string
  /** true = đang dùng bản người dùng sửa (DB); false = mẫu mặc định trong code. */
  is_custom: boolean
  /** Danh sách biến chèn được vào tiêu đề / thân, vd "code", "link". */
  variables: string[]
}

export interface EmailTemplatePreview {
  subject: string
  html: string
}
