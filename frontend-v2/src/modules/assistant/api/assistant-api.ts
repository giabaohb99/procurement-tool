import { apiDelete, apiGet, apiPost } from '@/core/api'
import type {
  AssistantAttachment,
  ChatReply,
  ChatRequest,
  ConversationDetail,
  ConversationSummary,
  ProvidersInfo,
} from '../types/assistant'

const BASE_URL = '/api/assistant'

export const assistantApi = {
  /** Nhà cung cấp + model mặc định. Trả 403 khi `AI_ENABLED` chưa bật. */
  providers: () => apiGet<ProvidersInfo>(`${BASE_URL}/providers`),

  /** Danh sách hội thoại của chính người dùng (mới trước). */
  conversations: () =>
    apiGet<{ items: ConversationSummary[] }>(`${BASE_URL}/conversations`),

  /** Một hội thoại kèm toàn bộ tin — chỉ chủ hội thoại xem được. */
  conversation: (id: number) =>
    apiGet<ConversationDetail>(`${BASE_URL}/conversations/${id}`),

  /** Gửi một câu hỏi; backend lưu vào hội thoại (mở mới nếu chưa có id). */
  chat: (body: ChatRequest) => apiPost<ChatReply>(`${BASE_URL}/chat`, body),

  /**
   * Tải MỘT tệp đính kèm chat (ảnh JPG/PNG/WebP <=5MB, PDF <=10MB) — tải TRƯỚC,
   * giữ id, rồi gắn `attachment_ids` khi gửi tin (khuôn tải-trước-gắn-sau của diễn đàn).
   */
  uploadAttachment: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return apiPost<AssistantAttachment>(`${BASE_URL}/uploads`, body)
  },

  /** Xóa hội thoại của chính mình. */
  remove: (id: number) => apiDelete<null>(`${BASE_URL}/conversations/${id}`),
}
