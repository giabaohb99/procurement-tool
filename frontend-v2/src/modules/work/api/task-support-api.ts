import { apiDelete, apiGet, apiPost } from '@/core/api'

import type {
  TaskAttachment,
  TaskComment,
  TaskCommentPage,
  TaskMentionablePerson,
  TaskUploadedFile,
} from '../types/task-support'

/**
 * Bình luận + đính kèm của một công việc — gọi thẳng hai API DÙNG CHUNG của hệ.
 *
 * Không có endpoint nào dưới `/api/work/` cho hai thứ này, và cố ý như vậy:
 * `tab_comment` / `tab_file_link` là bảng dùng chung, thêm một cửa riêng cho
 * phân hệ Dự án là chép lại cả một hệ con (đếm, nhắc tên, chuông, thu hồi tệp
 * mồ côi) chỉ để đổi cái tiền tố đường dẫn.
 */

const COMMENT_URL = '/api/comments'
const ATTACHMENT_URL = '/api/attachments'

/** Cả hai API đều nhận `entity` — với phân hệ này luôn là chuỗi dưới đây. */
export const TASK_ENTITY = 'work_task'

/** Số bình luận GỐC lấy mỗi lượt; backend cũng mặc định 10. */
export const COMMENT_PAGE_SIZE = 10

export const taskSupportApi = {
  // ── Bình luận ──────────────────────────────────────────────────────────────

  listComments: (taskId: number, beforeId = 0) =>
    apiGet<TaskCommentPage>(COMMENT_URL, {
      params: {
        entity: TASK_ENTITY,
        entity_id: taskId,
        limit: COMMENT_PAGE_SIZE,
        //  `0` là "không có con trỏ" — gửi đi thì backend hiểu là `id < 0` và
        //  trang nào cũng rỗng.
        before_id: beforeId || undefined,
      },
    }),

  /**
   * Gợi ý người để `@`.
   *
   * Chưa gõ chữ nào thì backend chỉ trả người ĐANG DÍNH tới việc (người tạo +
   * ai đã bình luận); gõ rồi thì tìm trong toàn bộ nhân sự.
   */
  listMentionable: (taskId: number, q = '') =>
    apiGet<TaskMentionablePerson[]>(`${COMMENT_URL}/mentionable`, {
      params: { entity: TASK_ENTITY, entity_id: taskId, q },
    }),

  createComment: (taskId: number, body: string, fileIds: number[] = []) =>
    apiPost<TaskComment>(COMMENT_URL, {
      entity: TASK_ENTITY,
      entity_id: taskId,
      body,
      file_ids: fileIds,
    }),

  deleteComment: (commentId: number) => apiDelete<null>(`${COMMENT_URL}/${commentId}`),

  /**
   * Tải tệp của một bình luận lên TRƯỚC, lấy `file_id`, rồi mới gửi bình luận.
   *
   * Bắt buộc đi hai nhịp: backend cấm gắn tệp vào bình luận bằng cửa chung
   * (`_deny_comment`) — tệp chỉ được gắn ngay lúc tạo, qua `file_ids`. Gắn cửa
   * khác là sinh ra link treo vào một bình luận chưa tồn tại.
   *
   * `entity: 'comment'` chứ không phải `work_task`: đây là chính sách tệp của
   * bình luận (đuôi cho phép, trần dung lượng), không phải của công việc.
   */
  uploadCommentFiles: (files: File[]) => {
    const body = new FormData()
    body.append('entity', 'comment')
    files.forEach((file) => body.append('files', file))
    return apiPost<TaskUploadedFile[]>(`${ATTACHMENT_URL}/upload-file`, body)
  },

  // ── Đính kèm cấp CÔNG VIỆC ─────────────────────────────────────────────────

  listAttachments: (taskId: number) =>
    apiGet<TaskAttachment[]>(ATTACHMENT_URL, {
      params: { entity: TASK_ENTITY, entity_id: taskId },
    }),

  /** Tải lên VÀ gắn luôn vào việc — việc đã có id nên không cần đi hai nhịp. */
  uploadAttachments: (taskId: number, files: File[]) => {
    const body = new FormData()
    body.append('entity', TASK_ENTITY)
    body.append('entity_id', String(taskId))
    body.append('doc_type', '')
    files.forEach((file) => body.append('files', file))
    return apiPost<TaskAttachment[]>(ATTACHMENT_URL, body)
  },

  deleteAttachment: (linkId: number) => apiDelete<null>(`${ATTACHMENT_URL}/${linkId}`),
}
