import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '@/core/api'
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
  /** Chuông ERP chuyển sang chat này: 0 tắt · 1 việc của tôi · 2 tất cả (ai-CR-059). */
  notify_mode: number
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

/** Một hãng AI bot nhận khóa (ai-CR-098): gemini · claude · openai · openrouter. */
export interface AiProviderInfo {
  name: string
  label: string
  /** Trang lấy khóa của hãng. */
  site: string
}

/** Một dòng khóa trong sổ `tab_ai_key` (ai-CR-098) — cá nhân hoặc công ty. Không bao giờ có khóa thô. */
export interface AiKeyItem {
  id: number
  provider: string
  provider_label: string
  /** Trống = model mặc định của hãng. */
  model: string
  /** 1 = khóa chính; 2, 3… dự phòng, hỏng thì bot tự nhảy sang. */
  priority: number
  /** Trần lượt/ngày riêng của khóa; 0 = theo trần chung. */
  daily_cap: number
  hint: string
  verified_at: string | null
  used_today: number
  /** Địa chỉ trạm — chỉ hãng «Tương thích OpenAI (tùy chỉnh)» (ai-CR-108). */
  base_url?: string
}

/** Khóa AI CÁ NHÂN của chính mình (ai-CR-053 → ai-CR-098 nhiều khóa). Khóa thô chỉ đi VÀO; chỉ 4 ký tự cuối đi ra. */
export interface AiKeyInfo {
  provider: string
  has_key: boolean
  /** `…9999` của khóa ưu tiên cao nhất — đủ để nhận ra, không đủ để dùng. */
  hint: string
  verified_at: string | null
  items?: AiKeyItem[]
  /** Số khóa công ty đang có — hết khóa cá nhân thì bot lùi về đây (có trần lượt/ngày). */
  company_keys?: number
  providers?: AiProviderInfo[]
}

/** Khóa AI CÔNG TY (ai-CR-098) — gác quyền cấu hình hệ thống. */
export interface CompanyAiKeys {
  items: AiKeyItem[]
  providers: AiProviderInfo[]
}

export interface AiKeyInput {
  key: string
  provider?: string
  /** Bắt buộc với hãng «openai_compat»: https://tên-miền/v1 (ai-CR-108). */
  base_url?: string
  model?: string
  priority?: number
  daily_cap?: number
}

export interface AiKeyPatch {
  model?: string
  priority?: number
  daily_cap?: number
}

/** Khóa kết nối MCP cá nhân (ai-CR-063). `key` chỉ có trong kết quả tạo, đúng một lần. */
export interface McpKeyItem {
  id: number
  name: string
  hint: string
  scope: number
  scope_label: string
  expires_at: string | null
  last_used_at: string | null
  created_at: string | null
  key?: string
}

export interface McpKeysResult {
  endpoint: string
  items: McpKeyItem[]
}

/** Kết nối Google cá nhân (ai-CR-064). */
export interface GoogleLinkInfo {
  configured: boolean
  linked: boolean
  email: string
  linked_at: string | null
}

export const agentHubApi = {
  list: (params: AgentTaskListParams) => apiGet<AgentTaskListResult>('/api/agent-hub/tasks', { params }),
  detail: (id: number) => apiGet<AgentTaskDetail>(`/api/agent-hub/tasks/${id}`),
  stats: (days: number) => apiGet<AgentStats>('/api/agent-hub/stats', { params: { days } }),

  /** Ba cửa liên kết Telegram của CHÍNH MÌNH — chỉ đòi đăng nhập, không cần khóa `agent_task`. */
  myLinks: () => apiGet<TelegramLinksResult>('/api/agent-hub/links'),
  createLinkCode: () => apiPost<TelegramLinkCode>('/api/agent-hub/links/code', {}),
  removeLink: (id: number) => apiDelete<null>(`/api/agent-hub/links/${id}`),
  setLinkNotifyMode: (id: number, notify_mode: number) => apiPatch<TelegramLink>(`/api/agent-hub/links/${id}`, { notify_mode }),

  /** Khóa AI cá nhân — tự phục vụ, chỉ đòi đăng nhập (ai-CR-053, nhiều khóa từ ai-CR-098). */
  myAiKey: () => apiGet<AiKeyInfo>('/api/agent-hub/ai-key'),
  setAiKey: (body: AiKeyInput) => apiPut<AiKeyInfo>('/api/agent-hub/ai-key', body),
  patchAiKey: (id: number, body: AiKeyPatch) => apiPatch<AiKeyInfo>(`/api/agent-hub/ai-key/${id}`, body),
  removeOneAiKey: (id: number) => apiDelete<AiKeyInfo>(`/api/agent-hub/ai-key/${id}`),
  removeAiKey: () => apiDelete<AiKeyInfo>('/api/agent-hub/ai-key'),

  /** Khóa AI công ty (ai-CR-098) — quyền cấu hình hệ thống. */
  companyAiKeys: () => apiGet<CompanyAiKeys>('/api/agent-hub/ai-key/company'),
  setCompanyAiKey: (body: AiKeyInput) => apiPut<CompanyAiKeys>('/api/agent-hub/ai-key/company', body),
  patchCompanyAiKey: (id: number, body: AiKeyPatch) => apiPatch<CompanyAiKeys>(`/api/agent-hub/ai-key/company/${id}`, body),
  removeCompanyAiKey: (id: number) => apiDelete<CompanyAiKeys>(`/api/agent-hub/ai-key/company/${id}`),

  /** Khóa MCP cá nhân — tự phục vụ (ai-CR-063). */
  myMcpKeys: () => apiGet<McpKeysResult>('/api/agent-hub/mcp-keys'),
  createMcpKey: (body: { name: string; scope: number; days: number }) => apiPost<McpKeyItem>('/api/agent-hub/mcp-keys', body),
  removeMcpKey: (id: number) => apiDelete<null>(`/api/agent-hub/mcp-keys/${id}`),

  /** Google cá nhân — Lịch + Drive (ai-CR-064). */
  myGoogle: () => apiGet<GoogleLinkInfo>('/api/agent-hub/google'),
  googleAuthorizeUrl: () => apiPost<{ url: string }>('/api/agent-hub/google/authorize', {}),
  disconnectGoogle: () => apiDelete<GoogleLinkInfo>('/api/agent-hub/google'),
}
