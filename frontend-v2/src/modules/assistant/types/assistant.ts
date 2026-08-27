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

/** Tệp đính kèm chat (CR-204) — kết quả `POST /uploads`, cũng là chip trên tin đã lưu. */
export interface AssistantAttachment {
  id: number
  filename: string
  content_type: string
  size: number
}

/** Một tin trong hội thoại (câu hỏi hoặc câu trả lời). */
export interface AssistantMessage {
  id: number
  role: number
  role_name: MessageRoleName
  content: string
  /** Tệp người dùng gửi kèm lượt hỏi — chỉ tin của user có, trợ lý luôn rỗng. */
  attachments: AssistantAttachment[]
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
  /** Id tệp đã tải qua `POST /uploads` gắn vào lượt hỏi này (tối đa 3). */
  attachment_ids?: number[]
}

/** Một lần trợ lý gọi công cụ trong lượt trả lời (backend chỉ trả tên + tham số). */
export interface AssistantToolCall {
  name: string
  args: Record<string, unknown>
  rows?: number | null
  /** Bản nháp ĐÃ CHUẨN HÓA từ kết quả tool soạn nháp (vd ĐVT khớp chính tả danh mục) —
   *  có thì dùng thay `args` thô do model gõ vào. */
  draft?: Record<string, unknown>
  /** File báo cáo tool `export_report_file` vừa sinh — dựng nút Tải báo cáo từ đây.
   *  `download_url` là endpoint cần Bearer, phải tải qua `downloadFile` chứ đừng gắn href. */
  file?: {
    id: number
    filename: string
    size: number
    download_url: string
  }
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
  /** Chỉ có ở lượt trả lời SỐNG — không lưu DB, tải lại hội thoại là mất. */
  tool_calls?: AssistantToolCall[]
}
