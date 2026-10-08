import { apiGet, apiPatch, apiPost } from '@/core/api'
import { downloadFile } from '@/core/api/download-file'

/**
 * NHÓM CHAT CỦA BOT (ai-CR-123) — `/api/agent-hub/groups*`, `/api/agent-hub/zalo/*`.
 *
 * Ai cũng xem được nhóm mình là thành viên (cùng luật với bot). Khóa `agent_group.read` = quản lý bot AI thấy
 * MỌI nhóm kể cả nội dung (có nhật ký xem); `agent_group.write` = phân loại, ngừng ghi, đăng nhập Zalo công ty.
 * Khớp `agent_hub/controller.py` + `agent_hub/groups.py`.
 */

export interface ChatGroupOption {
  value: number | string
  label: string
}

export interface ChatGroupMeta {
  categories: { value: number; label: string }[]
  channels: { value: string; label: string }[]
  can_view_all: boolean
  can_manage: boolean
  retention_days: number
  zalo_enabled: boolean
}

export interface ChatGroupItem {
  id: number
  title: string
  /** `telegram` · `zalo_account` (tài khoản Zalo công ty) · `zalo_bot` (bot Zalo chính thức). */
  channel: string
  channel_label: string
  category: number
  category_label: string
  /** false = bot đã rời / bị mời ra khỏi nhóm. */
  active: boolean
  /** true = người quản lý bot AI đã tắt ghi nhóm này. */
  paused: boolean
  is_member: boolean
  is_owner: boolean
  owner_user_id: number
  owner_label: string
  /** Chỉ nhóm Zalo có danh sách thành viên; Telegram là null. */
  members_count: number | null
  message_count: number
  file_count: number
  last_message_at: string | null
  joined_at: string | null
  can_edit: boolean
  can_pause?: boolean
}

export interface ChatGroupListResult {
  items: ChatGroupItem[]
  total: number
  can_view_all: boolean
  can_manage: boolean
}

export interface ChatGroupListParams {
  scope?: 'mine' | 'all'
  channel?: string
  category?: number
  q?: string
  include_inactive?: boolean
}

export interface ChatGroupFile {
  name: string
  kind: string
  mime: string
  size: number
}

export interface ChatGroupMessage {
  id: number
  from_name: string
  text: string
  sent_at: string | null
  file: ChatGroupFile | null
}

export interface ChatGroupMessagePage {
  items: ChatGroupMessage[]
  has_more: boolean
  next_before_id: number | null
}

export interface ChatGroupMessageParams {
  before_id?: number
  limit?: number
  q?: string
  files_only?: boolean
}

export interface ChatGroupSummary {
  id: number
  user_id: number
  user_label: string
  /** 1 = sinh ra khi hỏi bot / Trợ lý web · 2 = nút «Tóm tắt» trên màn này. */
  source: number
  hours: number
  question: string
  text: string
  created_at: string | null
}

export interface ChatGroupView {
  id: number
  user_id: number
  user_label: string
  what: string
  at: string | null
}

export interface ChatGroupSummarizeResult {
  text: string
  empty: boolean
  count: number
}

export interface ZaloAccountStatus {
  enabled: boolean
  /** off · unreachable · idle · qr · connected · down */
  state: string
  name?: string
  groups?: number | null
  queued?: number
  reason?: string
  /** PNG base64 (không kèm tiền tố data:) — chỉ trả cho người có `agent_group.write` khi đang chờ quét. */
  qr_image?: string
}

const BASE = '/api/agent-hub'

export const chatGroupApi = {
  meta: () => apiGet<ChatGroupMeta>(`${BASE}/groups/meta`),
  list: (params: ChatGroupListParams) => apiGet<ChatGroupListResult>(`${BASE}/groups`, { params }),
  detail: (id: number) => apiGet<ChatGroupItem>(`${BASE}/groups/${id}`),
  messages: (id: number, params: ChatGroupMessageParams) =>
    apiGet<ChatGroupMessagePage>(`${BASE}/groups/${id}/messages`, { params }),
  summaries: (id: number) => apiGet<{ items: ChatGroupSummary[] }>(`${BASE}/groups/${id}/summaries`),
  summarize: (id: number, hours: number) =>
    apiPost<ChatGroupSummarizeResult>(`${BASE}/groups/${id}/summarize`, { hours }),
  update: (id: number, body: { category?: number; paused?: boolean }) =>
    apiPatch<{ id: number; category: number; paused: boolean }>(`${BASE}/groups/${id}`, body),
  views: (id: number) => apiGet<{ items: ChatGroupView[] }>(`${BASE}/groups/${id}/views`),
  downloadFile: (groupId: number, messageId: number, filename: string) =>
    downloadFile(`${BASE}/groups/${groupId}/files/${messageId}`, filename),

  zaloStatus: () => apiGet<ZaloAccountStatus>(`${BASE}/zalo/status`),
  zaloLogin: () => apiPost<null>(`${BASE}/zalo/login`, {}),
  zaloRefreshGroups: () => apiPost<null>(`${BASE}/zalo/refresh-groups`, {}),
  zaloLogout: () => apiPost<null>(`${BASE}/zalo/logout`, {}),
}
