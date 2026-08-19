import { apiGet, apiPost, apiPut } from '@/core/api'

import type { SettingPayload, SettingTestResult } from '../types/setting'

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
}
