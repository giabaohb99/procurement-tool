import { apiGet, apiPut } from '@/core/api'

import type { SettingsPayloadForHr } from '../types/hr-setting'

/**
 * Cài đặt nhân sự (duoc-CR-713) đi CHUNG đường `/api/settings` với Cấu hình hệ thống — cùng kho `tab_setting`,
 * cùng nhật ký thay đổi, cùng khóa quyền `setting` (đọc / sửa). Lưu chỉ gửi ba khóa nhóm `hr`; backend nhận
 * một phần danh sách và trả lại trạng thái đầy đủ.
 */
export const hrSettingApi = {
  get: () => apiGet<SettingsPayloadForHr>('/api/settings'),
  save: (values: Record<string, unknown>) => apiPut<SettingsPayloadForHr>('/api/settings', { values }),
}
