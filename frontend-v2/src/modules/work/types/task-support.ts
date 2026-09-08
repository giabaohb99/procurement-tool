/**
 * Bình luận (E-01) và đính kèm (E-03) của một CÔNG VIỆC.
 *
 * Hai thứ này KHÔNG có bảng riêng của phân hệ Dự án: chúng dùng đúng hạ tầng
 * chung của cả hệ — `tab_comment` qua `/api/comments`, `tab_file` + `tab_file_link`
 * qua `/api/attachments` — với `entity = "work_task"`. Bảng khai ở
 * `backend/app/core/comment_registry.py` và `core/file_registry.py`.
 *
 * ⚠️ Quyền KHÔNG đi đường `apply_scope` như mọi chứng từ khác: phạm vi thật của
 * phân hệ này là TƯ CÁCH THÀNH VIÊN của dự án, nên backend rẽ nhánh riêng
 * (`comment/service.resolve_doc` và `core/attachment_scope._ensure_task_member`).
 * Khách xem đọc được nhưng không gửi/gắn được — xem `canEdit` ở tầng component.
 */

/** Tệp gắn trong MỘT bình luận — khuôn `_file_out` của backend. */
export interface TaskCommentFile {
  link_id: number
  filename: string
  url: string
  content_type: string
  size: number
  is_image: boolean
}

/** Người được nhắc bằng `@` trong một bình luận. */
export interface TaskCommentMention {
  user_id: number
  name: string
}

/** Một người trong danh sách gợi ý khi gõ `@`. */
export interface TaskMentionablePerson {
  user_id: number
  name: string
  code: string
  avatar: string
  /** Đã dính tới việc này (người tạo / đã bình luận) — xếp lên đầu. */
  related: boolean
}

export interface TaskComment {
  id: number
  body: string
  author_id: number
  author_name: string
  author_code: string
  author_avatar: string
  created_at: string
  /** Backend tự quyết: tác giả, hoặc người có quyền xóa của quản trị. */
  can_delete: boolean
  mentions: TaskCommentMention[]
  files: TaskCommentFile[]
}

/**
 * Một trang bình luận. `older_count` / `oldest_id` phục vụ nút «Xem N bình luận
 * trước» — phân trang theo CON TRỎ chứ không `offset`, nên có người gửi thêm
 * giữa chừng cũng không làm lệch trang.
 */
export interface TaskCommentPage {
  items: TaskComment[]
  total: number
  older_count: number
  oldest_id: number
}

/** Tệp đính kèm ở cấp CÔNG VIỆC (không thuộc bình luận nào). */
export interface TaskAttachment {
  id: number
  file_id: number
  filename: string
  /** Đường đọc thẳng kho lưu trữ. Rỗng thì phải tải qua đường có kiểm quyền. */
  url: string
  content_type: string
  size: number
}

/** Tệp vừa tải lên nhưng CHƯA gắn vào đâu — bước một của lối "tải trước, gắn sau". */
export interface TaskUploadedFile {
  file_id: number
  filename: string
  url: string
  content_type: string
  size: number
}
