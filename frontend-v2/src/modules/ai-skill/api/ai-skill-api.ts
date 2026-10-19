import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '@/core/api'
import type {
  AdminMcpKey,
  AiOverview,
  McpLastCall,
  McpSettings,
  McpSettingsPatch,
  McpSetupDetail,
  McpSetupList,
  MyMcpKey,
  VisibleSkill,
  KeyAdminMeta,
  KeyIssueInput,
  KeyIssueResult,
  KeyRevokeInput,
  McpCallFilters,
  McpCallPage,
  PagedItems,
  Skill,
  SkillAccess,
  SkillAccessGrantInput,
  SkillAccessGrantResult,
  SkillDetail,
  SkillFile,
  SkillImportResult,
  SkillInput,
  SkillPatch,
  SkillSet,
  SkillSetInput,
  SkillSetPatch,
  SkillVersion,
  SkillVersionItem,
} from '../types/ai-skill'

const BASE = '/api/ai-skills'
const HUB = '/api/agent-hub'

/** Bỏ các tham số rỗng — backend coi `?state=` là lỗi kiểu số (422), không phải "không lọc". */
function compact(params: object): Record<string, unknown> {
  return Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''))
}

/** Kho skill AI — đường `/api/ai-skills` (K1 bao-CR-621). */
export const aiSkillApi = {
  listSets: () => apiGet<{ items: SkillSet[] }>(`${BASE}/sets`),
  getSet: (id: number) => apiGet<SkillSet>(`${BASE}/sets/${id}`),
  createSet: (body: SkillSetInput) => apiPost<SkillSet>(`${BASE}/sets`, body),
  updateSet: (id: number, body: SkillSetPatch) => apiPatch<SkillSet>(`${BASE}/sets/${id}`, body),
  deleteSet: (id: number) => apiDelete<null>(`${BASE}/sets/${id}`),

  listSkills: (setId: number) => apiGet<{ items: Skill[] }>(`${BASE}/sets/${setId}/skills`),
  createSkill: (setId: number, body: SkillInput) => apiPost<SkillDetail>(`${BASE}/sets/${setId}/skills`, body),
  /** Tải gói `.zip` / `.skill`. Trùng tên skill trong bộ = THAY GÓI (ghi đè nháp + thay toàn bộ tệp đi kèm). */
  importPackage: (setId: number, file: File, slug = '') => {
    const form = new FormData()
    form.append('file', file)
    return apiPost<SkillImportResult>(`${BASE}/sets/${setId}/import`, form, { params: compact({ slug }) })
  },
  getSkill: (id: number) => apiGet<SkillDetail>(`${BASE}/skills/${id}`),
  updateSkill: (id: number, body: SkillPatch) => apiPatch<SkillDetail>(`${BASE}/skills/${id}`, body),
  deleteSkill: (id: number) => apiDelete<null>(`${BASE}/skills/${id}`),
  publishSkill: (id: number, changeNote: string) =>
    apiPost<{ version_id: number; version_no: number }>(`${BASE}/skills/${id}/publish`, { change_note: changeNote }),
  listVersions: (skillId: number) => apiGet<{ items: SkillVersionItem[] }>(`${BASE}/skills/${skillId}/versions`),
  getVersion: (versionId: number) => apiGet<SkillVersion>(`${BASE}/versions/${versionId}`),
  putFile: (skillId: number, path: string, contentText: string) =>
    apiPut<SkillFile>(`${BASE}/skills/${skillId}/files`, { path, content_text: contentText }),
  deleteFile: (skillId: number, fileId: number) => apiDelete<null>(`${BASE}/skills/${skillId}/files/${fileId}`),

  listAccess: (targetKind: number, targetId: number) =>
    apiGet<{ items: SkillAccess[] }>(`${BASE}/access`, { params: { target_kind: targetKind, target_id: targetId } }),
  grantAccess: (body: SkillAccessGrantInput) => apiPost<SkillAccessGrantResult>(`${BASE}/access`, body),
  revokeAccess: (id: number, reason = '') => apiDelete<null>(`${BASE}/access/${id}`, { data: { reason } }),
}

/** Khóa kết nối AI của nhân sự (K4 ai-CR-212) + nhật ký lượt gọi (K3 ai-CR-209) — qua cổng `/api/agent-hub`. */
export const aiUsageApi = {
  keyAdminMeta: () => apiGet<KeyAdminMeta>(`${HUB}/mcp-key-admin/meta`),
  keyAdminKeys: (params: { department_id?: number; state?: number; user_id?: number; page: number; size: number }) =>
    apiGet<PagedItems<AdminMcpKey>>(`${HUB}/mcp-key-admin/keys`, { params: compact(params) }),
  issueKeys: (body: KeyIssueInput) => apiPost<KeyIssueResult>(`${HUB}/mcp-key-admin/issue`, body),
  revokeKeys: (body: KeyRevokeInput) => apiPost<{ revoked: number }>(`${HUB}/mcp-key-admin/revoke`, body),
  listCalls: (filters: McpCallFilters) => apiGet<McpCallPage>(`${HUB}/mcp-calls`, { params: compact(filters) }),
  /** Cấu hình cổng MCP (G7): đọc cần `agent_group.read`, lưu cần `agent_group.write`. */
  settings: () => apiGet<McpSettings>(`${HUB}/mcp-settings`),
  saveSettings: (body: McpSettingsPatch) => apiPut<McpSettings>(`${HUB}/mcp-settings`, body),
}

/**
 * «AI của tôi» (G8) + Tổng quan (G1) — K6, hợp đồng doc/agent-hub/06 §6. Khóa của CHÍNH MÌNH đi chung đường
 * `mcp-keys` với tab cũ (ai-CR-063), nay kèm trạng thái và khóa chờ nhận do quản trị phát hộ.
 */
export const myAiApi = {
  setupClients: () => apiGet<McpSetupList>(`${HUB}/mcp-setup`),
  setup: (client: string) => apiGet<McpSetupDetail>(`${HUB}/mcp-setup`, { params: { client } }),
  myKeys: () => apiGet<{ endpoint: string; items: MyMcpKey[] }>(`${HUB}/mcp-keys`),
  createKey: (body: { name: string; scope: number; days: number }) => apiPost<MyMcpKey>(`${HUB}/mcp-keys`, body),
  removeKey: (id: number) => apiDelete<null>(`${HUB}/mcp-keys/${id}`),
  pendingKeys: () => apiGet<{ items: MyMcpKey[] }>(`${HUB}/mcp-keys/pending`),
  /** Nhận khóa quản trị phát hộ — khóa thô trả về ĐÚNG một lần, lần hai 404. */
  claimKey: (id: number) => apiPost<MyMcpKey>(`${HUB}/mcp-keys/${id}/claim`),
  lastCall: (id: number) => apiGet<McpLastCall>(`${HUB}/mcp-keys/${id}/last-call`),
  visibleSkills: () => apiGet<{ items: VisibleSkill[] }>(`${BASE}/me`),
  overview: () => apiGet<AiOverview>(`${HUB}/ai-overview`),
}
