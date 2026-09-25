import { apiDelete, apiGet, apiPost, apiPut } from '@/core/api'
import type { ListParams } from '@/shared/types/api'

/**
 * VIỆC CỦA BOT Agent Hub (ai-CR-036) — `/api/agent-hub/*`, khóa `agent_task`.
 *
 * Chỉ ĐỌC. Duyệt, gộp, thu hồi, bỏ… vẫn đi qua Telegram, nơi có luật hỏi-trước và
 * dấu vết hội thoại. Màn này để tra: bot đã nhận gì, qua bước nào, mất bao lâu, tốn bao nhiêu.
 */

/** Khớp `serialize_task` ở `backend/app/modules/agent_hub/controller.py`. */
export interface AgentTaskItem {
  id: number
  code: string
  title: string
  status: number
  status_label: string
  risk_level: number
  risk_label: string
  source: number
  source_label: string
  branch_name: string
  pr_url: string
  created_at: string | null
  updated_at: string | null
  closed_at: string | null
  deployed_dev_at: string | null
  /** Tổng chi phí model ƯỚC theo bảng giá (USD) — Claude Code chạy gói thuê bao, số chỉ để so. */
  cost_usd: number
  /** Tổng thời gian bot thật sự chạy (ms), không tính lúc nằm chờ. */
  bot_ms: number
  runs: number
}

export interface AgentTaskListResult {
  items: AgentTaskItem[]
  total: number
  page: number
  page_size: number
  statuses: { value: number; label: string }[]
}

export interface AgentRunRow {
  id: number
  stage: number
  stage_label: string
  status: number
  status_label: string
  provider: string
  model: string
  started_at: string | null
  duration_ms: number
  input_tokens: number
  output_tokens: number
  cost_usd: number
  error: string
}

export interface AgentMessageRow {
  id: number
  /** 1 = bot gửi, 2 = đại ca gửi (`DIR_OUT` / `DIR_IN`). */
  direction: number
  direction_label: string
  action: string
  /** Thân tin — tin của bot là HTML Telegram, đã cắt 2000 ký tự. */
  body: string
  files: number
  created_at: string | null
}

export interface AgentTaskDetail extends AgentTaskItem {
  summary: string
  plan: string
  plan_files: string[]
  test_plan: string
  questions: string[]
  note: string
  scan_message: string
  merged_sha: string
  timing: string
  sources: { source: number; source_label: string; ref_id: number }[]
  run_list: AgentRunRow[]
  messages: AgentMessageRow[]
}

export interface AgentStats {
  days: number
  total_cost_usd: number
  run_count: number
  by_status: { status: number; label: string; count: number }[]
  cost_by_day: { day: string; cost_usd: number }[]
  cost_by_stage: { stage: number; label: string; cost_usd: number }[]
}

export interface AgentTaskListParams extends ListParams {
  /** 0 = mọi trạng thái. */
  status?: number
  q?: string
}

/** Khớp `DIR_IN` ở `agent_hub/constants.py`. */
export const AGENT_DIR_IN = 2

/** Một liên kết Telegram còn hiệu lực của chính mình (ai-CR-038). `chat` đã che còn 4 số cuối. */
export interface TelegramLink {
  id: number
  chat: string
  tg_name: string
  linked_at: string | null
  expires_at: string | null
}

export interface TelegramLinksResult {
  enabled: boolean
  /** Tên bot không có `@`; rỗng thì không dựng được link mở thẳng bot. */
  bot_username: string
  items: TelegramLink[]
}

export interface TelegramLinkCode {
  code: string
  expires_at: string | null
  /** `https://t.me/<bot>?start=<mã>` — bấm là Telegram tự gửi `/start <mã>`. Rỗng nếu chưa khai tên bot. */
  deep_link: string
}

/** Khóa Gemini CÁ NHÂN của chính mình (ai-CR-053, D-01). Khóa thô chỉ đi VÀO; chỉ 4 ký tự cuối đi ra. */
export interface AiKeyInfo {
  provider: string
  has_key: boolean
  /** `…9999` — đủ để nhận ra khóa nào, không đủ để dùng. */
  hint: string
  verified_at: string | null
}

export const agentHubApi = {
  list: (params: AgentTaskListParams) => apiGet<AgentTaskListResult>('/api/agent-hub/tasks', { params }),
  detail: (id: number) => apiGet<AgentTaskDetail>(`/api/agent-hub/tasks/${id}`),
  stats: (days: number) => apiGet<AgentStats>('/api/agent-hub/stats', { params: { days } }),

  /** Ba cửa liên kết Telegram của CHÍNH MÌNH — chỉ đòi đăng nhập, không cần khóa `agent_task`. */
  myLinks: () => apiGet<TelegramLinksResult>('/api/agent-hub/links'),
  createLinkCode: () => apiPost<TelegramLinkCode>('/api/agent-hub/links/code', {}),
  removeLink: (id: number) => apiDelete<null>(`/api/agent-hub/links/${id}`),

  /** Khóa Gemini cá nhân — tự phục vụ, chỉ đòi đăng nhập (ai-CR-053). */
  myAiKey: () => apiGet<AiKeyInfo>('/api/agent-hub/ai-key'),
  setAiKey: (key: string) => apiPut<AiKeyInfo>('/api/agent-hub/ai-key', { key }),
  removeAiKey: () => apiDelete<AiKeyInfo>('/api/agent-hub/ai-key'),
}
