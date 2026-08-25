import { apiDelete, apiGet, apiPost } from '@/core/api'
import type {
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

  /** Xóa hội thoại của chính mình. */
  remove: (id: number) => apiDelete<null>(`${BASE_URL}/conversations/${id}`),
}
