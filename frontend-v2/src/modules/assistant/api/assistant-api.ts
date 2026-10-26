import type { AxiosRequestConfig } from 'axios'

import { apiDelete, apiGet, apiPost } from '@/core/api'
import type {
  AssistantAttachment,
  ChatReply,
  ChatRequest,
  ConfirmAccountSetupResult,
  ConfirmApprovalResult,
  ConfirmUpdateResult,
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

  /**
   * Bấm 'Xác nhận sửa' trên thẻ đề xuất (CR-218) — chỉ gửi token; mọi dữ liệu sửa nằm
   * TRONG token, backend kiểm lại quyền/phạm vi/trạng thái rồi mới ghi.
   */
  confirmUpdate: (token: string) =>
    apiPost<ConfirmUpdateResult>(`${BASE_URL}/confirm-update`, { token }),

  /**
   * Bấm 'Xác nhận duyệt / từ chối' trên thẻ đề xuất duyệt (kh-AI2-7) — cùng đường `confirm-update`, backend rẽ theo
   * loại token. Tắt toast tự động: thẻ tự báo lỗi tại chỗ (409 = phiếu đã đổi, phải hỏi lại AI).
   */
  confirmApproval: (token: string) =>
    apiPost<ConfirmApprovalResult>(`${BASE_URL}/confirm-update`, { token }, { _silent: true } as AxiosRequestConfig),

  /**
   * Bấm 'Xác nhận' trên thẻ đề xuất lập bộ tài khoản (bao-CR-435) — cùng khuôn: chỉ gửi
   * token, backend kiểm lại quyền / phạm vi / chống tự nâng quyền rồi mới gán.
   */
  confirmAccountSetup: (token: string) =>
    apiPost<ConfirmAccountSetupResult>(`${BASE_URL}/confirm-account-setup`, { token }),

  /** Xóa hội thoại của chính mình. */
  remove: (id: number) => apiDelete<null>(`${BASE_URL}/conversations/${id}`),
}
