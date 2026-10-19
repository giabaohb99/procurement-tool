/**
 * Kiểu dữ liệu của Kho skill AI — khớp đúng đầu ra backend `app/modules/ai_skill` (K1 bao-CR-621) và hai nhóm đường
 * `/api/agent-hub/mcp-key-admin/*` (K4 ai-CR-212), `/api/agent-hub/mcp-calls*` (K3 ai-CR-209).
 * Mọi mã trạng thái là SỐ (luật R2), nhãn tiếng Việt backend trả kèm ở trường `*_label`.
 */

export interface SkillSet {
  id: number
  code: string
  name: string
  description: string
  company_id: number
  owner_department_id: number
  status: number
  status_label: string
  security_level: number
  security_level_label: string
  sort_order: number
  skill_count: number
  created_at: string | null
  updated_at: string | null
}

export interface SkillSetInput {
  code?: string
  name: string
  description?: string
  company_id?: number
  owner_department_id?: number
  status: number
  security_level: number
  sort_order?: number
}

export type SkillSetPatch = Partial<Omit<SkillSetInput, 'code' | 'company_id'>>

export interface Skill {
  id: number
  skill_set_id: number
  slug: string
  title: string
  summary: string
  status: number
  status_label: string
  current_version_id: number | null
  version_no: number
  published_at: string | null
  has_unpublished_changes: boolean
  draft_updated_at: string | null
  sort_order: number
}

export interface SkillFile {
  id: number
  path: string
  size: number
  updated_at?: string | null
}

export interface SkillDetail extends Skill {
  draft_body_md: string
  files: SkillFile[]
}

export interface SkillInput {
  slug: string
  title?: string
  summary?: string
  body_md?: string
  sort_order?: number
}

export interface SkillPatch {
  title?: string
  summary?: string
  body_md?: string
  status?: number
  sort_order?: number
}

export interface SkillVersionItem {
  id: number
  version_no: number
  title: string
  change_note: string
  published_at: string | null
  published_by: number
  is_current: boolean
}

export interface SkillVersion {
  id: number
  skill_id: number
  version_no: number
  title: string
  summary: string
  body_md: string
  change_note: string
  published_at: string | null
}

export interface SkillImportResult {
  skill_id: number
  slug: string
  replaced: boolean
  files: number
  skipped: string[]
}

export interface SkillAccess {
  id: number
  target_kind: number
  target_kind_label: string
  target_id: number
  subject_kind: number
  subject_kind_label: string
  subject_id: number
  subject_name: string
  include_children: boolean
  effect: number
  effect_label: string
  valid_from: string | null
  valid_to: string | null
  reason: string
}

export interface SkillAccessGrantInput {
  target_kind: number
  target_id: number
  subjects: { subject_kind: number; subject_id: number }[]
  effect: number
  include_children: boolean
  reason?: string
  valid_from?: string | null
  valid_to?: string | null
}

export interface SkillAccessGrantResult {
  created: number
  updated: number
  skipped: number
}

/** Danh sách có tổng — phong bì chung của các đường phân trang phía dịch vụ AI. */
export interface PagedItems<T> {
  total: number
  page: number
  size: number
  has_more: boolean
  items: T[]
}

export interface KeyAdminMeta {
  days: number[]
  batch_max: number
  max_keys: number
  states: { value: number; label: string }[]
  can_read: boolean
  can_create: boolean
  can_delete: boolean
}

export interface AdminMcpKey {
  id: number
  name: string
  hint: string
  scope: number
  scope_label: string
  expires_at: string | null
  last_used_at: string | null
  created_at: string | null
  state: number
  state_label: string
  issued_by: number
  claimed_at: string | null
  batch_id: string
  user_id: number
  owner_label: string
  department_id: number
  department: string
  issued_by_label: string
}

export interface KeyIssueInput {
  user_ids?: number[]
  /** Mã HỒ SƠ nhân sự (ai-CR-215) — có thì máy chủ bỏ qua `department_id`. */
  employee_ids?: number[]
  department_id?: number
  days: number
  name?: string
}

export interface KeyIssueResult {
  batch_id: string
  issued: { user_id: number; employee_id?: number; label: string; key_id: number }[]
  /** Nhân sự chưa có tài khoản / tài khoản đã khóa → `user_id = 0` kèm lý do. */
  skipped: { user_id: number; employee_id?: number; label: string; reason: string }[]
}

export interface KeyRevokeInput {
  key_ids?: number[]
  user_id?: number
  batch_id?: string
}

export interface McpCall {
  id: number
  created_at: string | null
  key_id: number
  user_id: number
  employee_id: number
  department_id: number
  company_id: number
  client_name: string
  method: string
  tool: string
  skill_id: number
  status: number
  status_label: string
  deny_reason: string
  duration_ms: number
  ip: string
  user_label: string
}

export interface McpCallPage extends PagedItems<McpCall> {
  statuses: { value: number; label: string }[]
}

export interface McpCallFilters {
  date_from?: string
  date_to?: string
  user_id?: number
  key_id?: number
  tool?: string
  status?: number
  page: number
  size: number
}

// ---------------------------------------------------------------------------------------------------------------------
// K6 (doc/agent-hub/06 §6.1–6.2, ai-CR-213): màn «AI của tôi» ở Trang cá nhân + Tổng quan.
// ---------------------------------------------------------------------------------------------------------------------

/** Khóa kết nối AI CỦA CHÍNH MÌNH (`Key` §6.1). `key` (khóa thô) chỉ có trong kết quả tạo / nhận, đúng một lần. */
export interface MyMcpKey {
  id: number
  name: string
  hint: string
  scope: number
  scope_label: string
  expires_at: string | null
  last_used_at: string | null
  created_at: string | null
  state: number
  state_label: string
  issued_by: number
  claimed_at: string | null
  batch_id: string
  user_id: number
  key?: string
}

export interface McpSetupClient {
  client: string
  label: string
  supported: boolean
}

export interface McpSetupList {
  endpoint: string
  placeholder: string
  clients: McpSetupClient[]
}

export interface McpSetupDetail {
  client: string
  label: string
  supported: boolean
  /** `json` = đoạn cấu hình dán vào tệp, `shell` = câu lệnh chạy trong cửa sổ dòng lệnh. */
  format: 'json' | 'shell' | ''
  snippet: string
  steps: string[]
  files?: { windows?: string; macos?: string; all?: string }
  requires?: string[]
  note?: string
  endpoint: string
  placeholder: string
}

/** Một lượt gọi rút gọn (`Call` §6.1). */
export interface McpCallBrief {
  created_at: string | null
  client_name: string
  method: string
  tool: string
  status: number
  status_label: string
  deny_reason: string
}

export interface McpLastCall {
  key_id: number
  connected: boolean
  last_call: McpCallBrief | null
  last_ok_call: McpCallBrief | null
}

/** Skill AI của người đang xem đọc được (`GET /api/ai-skills/me`). */
export interface VisibleSkill {
  skill_id: number
  slug: string
  title: string
  summary: string
  version_no: number
  version_id: number
  updated_at: string | null
  skill_set_id: number
  skill_set: string
  security_level: number
  security_level_label: string
}

export interface DailyCalls {
  day: string
  total: number
  ok: number
  denied: number
  error: number
}

export interface AiOverview {
  generated_at: string
  skills: { skill_sets: number; skills: number } | null
  connected_users: number
  connected_days: number
  calls_7d: number
  calls_prev_7d: number
  calls_change_pct: number | null
  denied_7d: number
  error_7d: number
  daily: DailyCalls[]
  top_tools: { key: string; calls: number }[]
  top_users: { key: number; calls: number; label: string }[]
  top_skills: { skill_id: number; calls: number }[]
  keys_by_state: { state: number; label: string; count: number }[]
  expiring_keys: { key_id: number; user_id: number; owner_label: string; name: string; expires_at: string | null; state: number }[]
  expiring_days: number
}

/** Cấu hình cổng MCP (G7, doc/agent-hub/06 §7.3 — ai-CR-216). */
export interface McpToolGroup {
  key: string
  label: string
  enabled: boolean
  /** Mặc định khi chưa ai lưu. */
  default: boolean
  tools: string[]
}

export interface McpLimit {
  key: string
  label: string
  value: number
  default: number
  min: number
  max: number
}

export interface McpSettings {
  groups: McpToolGroup[]
  limits: McpLimit[]
  extra_instructions: string
  extra_max_len: number
  /** Chỉ GET có; PUT trả bản không kèm trường này. */
  can_write?: boolean
}

/** Lưu một phần: trường không gửi thì máy chủ giữ nguyên. Trần gửi theo khóa ở `McpLimit.key`. */
export type McpSettingsPatch = {
  groups?: Record<string, boolean>
  extra_instructions?: string
} & { [limitKey: string]: number | string | Record<string, boolean> | undefined }

/**
 * Ứng dụng AI tự đăng ký OAuth (ai-CR-225, màn bao-CR-635): `GET /api/agent-hub/oauth-clients`. `client_name` là do ứng
 * dụng TỰ KHAI — không tin; `redirect_hosts` là nơi quay về đã rút về hostname (máy cục bộ ghi «máy tính của bạn»),
 * `trusted` = mọi host thuộc ứng dụng AI quen (chatgpt.com, openai.com, claude.ai, anthropic.com, claude.com) hoặc máy cục bộ.
 */
export interface OAuthClient {
  id: number
  client_id: string
  client_name: string
  redirect_hosts: string[]
  trusted: boolean
  auth_method: string
  ip: string
  created_at: string | null
  last_used_at: string | null
  /** Kết nối (mã truy cập) còn sống của ứng dụng — xóa ứng dụng là cắt hết. */
  live_grants: number
}

export interface OAuthClientList {
  items: OAuthClient[]
  can_delete: boolean
}
