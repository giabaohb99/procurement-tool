import { apiDelete, apiGet, apiPost } from '@/core/api'

import type { EmailExclusion, ExclusionScope } from '../types/email-exclusion'

/**
 * Loại trừ email — không gửi email thông báo cho một cá nhân / phòng ban / công ty
 * (theo hồ sơ nhân sự). Chỉ chặn email; chuông trong ứng dụng vẫn gửi.
 */
export const emailExclusionApi = {
  list: () => apiGet<EmailExclusion[]>('/api/email-exclusions'),

  add: (body: { scope: ExclusionScope; ref_id: number; label: string; event: string }) =>
    apiPost<EmailExclusion>('/api/email-exclusions', body),

  remove: (id: number) => apiDelete<null>(`/api/email-exclusions/${id}`),
}
