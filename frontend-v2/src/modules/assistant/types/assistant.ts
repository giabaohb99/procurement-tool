/**
 * Kiểu dữ liệu của phân hệ Trợ lý AI (khớp serializer backend
 * `app/modules/assistant/conversation.py` + endpoint `/chat`, `/providers`).
 */

/** Vai trò tin nhắn — số khớp `MessageRole` (IntEnum) của backend. */
export type MessageRoleName = 'user' | 'assistant'

/** Token đã dùng của một lượt trả lời — để soi chi phí, gồm cả token cache. */
export interface AssistantUsage {
  input_tokens: number
  output_tokens: number
  thinking_tokens: number
  cache_read_tokens: number
  cache_write_tokens: number
}

/** Một nhà cung cấp model (Claude / Gemini) và trạng thái đã có key hay chưa. */
export interface AssistantProvider {
  name: string
  default_model: string
  configured: boolean
}

/** Kết quả `/providers` — dựng ô chọn nhà + biết nhà mặc định. */
export interface ProvidersInfo {
  providers: AssistantProvider[]
  default_provider: string
}

/** Dòng tóm tắt một hội thoại trong danh sách bên trái. */
export interface ConversationSummary {
  id: number
  title: string
  provider: string | null
  model: string | null
  last_message_at: string | null
  created_at: string | null
}

/** Một tin trong hội thoại (câu hỏi hoặc câu trả lời). */
export interface AssistantMessage {
  id: number
  role: number
  role_name: MessageRoleName
  content: string
  provider: string | null
  model: string | null
  usage: AssistantUsage
  created_at: string | null
}

/** Chi tiết một hội thoại kèm toàn bộ tin. */
export interface ConversationDetail extends ConversationSummary {
  messages: AssistantMessage[]
}

/** Thân yêu cầu gửi một câu hỏi. `conversation_id` rỗng = mở hội thoại mới. */
export interface ChatRequest {
  message: string
  provider?: string
  /** lookup (loại A) | advice (loại B) | general. */
  kind?: 'lookup' | 'advice' | 'general'
  conversation_id?: number
}

/** Kết quả một lượt `/chat`. */
export interface ChatReply {
  text: string
  provider: string
  model: string
  kind: string
  usage: AssistantUsage
  conversation_id: number
  title: string
}
