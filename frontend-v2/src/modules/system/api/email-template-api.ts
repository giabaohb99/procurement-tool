import { apiGet, apiPost, apiPut } from '@/core/api'

import type { EmailTemplate, EmailTemplatePreview } from '../types/email-template'

/**
 * Mẫu email thông báo theo bước (phân hệ Đặt xe). Backend gộp mẫu mặc định (code)
 * với bản người dùng đã sửa (DB) rồi trả bản có hiệu lực. Chỉ event đã khai mới có.
 */
export const emailTemplateApi = {
  list: () => apiGet<EmailTemplate[]>('/api/email-templates'),

  get: (event: string) => apiGet<EmailTemplate>(`/api/email-templates/${event}`),

  update: (event: string, body: { enabled: boolean; subject: string; body_html: string }) =>
    apiPut<EmailTemplate>(`/api/email-templates/${event}`, body),

  reset: (event: string) => apiPost<EmailTemplate>(`/api/email-templates/${event}/reset`),

  /** Render thử bản đang soạn (gửi kèm) với dữ liệu mẫu — không đụng dữ liệu thật. */
  preview: (event: string, body: { subject?: string; body_html?: string }) =>
    apiPost<EmailTemplatePreview>(`/api/email-templates/${event}/preview`, body),

  /** Gửi email thử về đúng địa chỉ của người đang bấm. */
  testSend: (event: string) => apiPost<{ to_email: string }>(`/api/email-templates/${event}/test-send`),
}
