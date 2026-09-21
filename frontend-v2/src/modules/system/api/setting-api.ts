import { apiGet, apiPost, apiPut } from '@/core/api'

import type {
  RagIndexStatus,
  RagReindexMode,
  SettingPayload,
  SettingTestResult,
} from '../types/setting'

/**
 * Cấu hình hệ thống. Backend giữ toàn bộ danh sách trường (`FIELDS` /
 * `SECRET_FIELDS` trong `modules/setting/service.py`), frontend chỉ vẽ lại —
 * thêm một cấu hình mới ở backend là màn này tự có, không phải sửa gì ở đây.
 */
export const settingApi = {
  get: () => apiGet<SettingPayload>('/api/settings'),

  /** Lưu xong backend trả lại nguyên trạng thái mới — dùng luôn, khỏi tải lại. */
  save: (values: Record<string, unknown>) =>
    apiPut<SettingPayload>('/api/settings', { values }),

  /**
   * Gửi thử một email. Lỗi SMTP KHÔNG làm hỏng lời gọi (backend vẫn trả 200 kèm
   * `ok: false`), nên phải đọc `ok` chứ đừng chỉ bắt exception.
   */
  testEmail: (to: string) =>
    apiPost<SettingTestResult>('/api/settings/test-email', { to }),

  testStorage: () => apiPost<SettingTestResult>('/api/settings/test-storage'),

  /**
   * Nạp chỉ mục tìm kiếm tài liệu của Trợ lý AI (HDSD + FAQ) — đường A.
   *
   * `missing` = nạp bù, chỉ những bài chưa có trong kho; `all` = dựng lại toàn bộ.
   * Gần như lúc nào cũng nên dùng `missing`: nhúng là lời gọi mạng có trần request/phút,
   * dựng lại cả kho chỉ vì vừa thêm vài bài là cách chắc chắn nhất để dính lỗi quá hạn mức.
   *
   * Chạy NỀN ở worker: backend chỉ xếp hàng rồi trả `task_id` ngay, không chờ nhúng xong.
   * RAG chưa bật thì backend trả 400 (http client tự hiện toast lỗi).
   */
  reindexDocs: (mode: RagReindexMode) =>
    apiPost<{ task_id: string; mode: RagReindexMode }>(
      `/api/assistant/rag/reindex?mode=${mode}`,
    ),

  /**
   * Đối chiếu số bài dưới DB với số nguồn đang nằm trong kho vector.
   * RAG tắt thì trả `{ enabled: false }` chứ không lỗi — thẻ vẫn vẽ được, chỉ đổi lời.
   */
  ragIndexStatus: () => apiGet<RagIndexStatus>('/api/assistant/rag/index-status'),
}
