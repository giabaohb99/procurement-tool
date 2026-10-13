import { apiGet, apiPost } from '@/core/api'

/**
 * Sổ thay đổi do bot ghi + hoàn tác 24 giờ (ai-CR-182 / ai-CR-185, phase 15) — hợp đồng ở
 * `doc/agent-hub/18-so-thay-doi-va-hoan-tac.md` §3.
 *
 * Mặc định chỉ trả dòng của CHÍNH người gọi. `all = true` (của mọi người) chỉ cho người có
 * `agent_group.read` — thiếu khóa thì backend trả 403, nên tầng giao diện phải gác bằng `can()`
 * trước khi bật tham số này, đừng để người thường ăn một toast lỗi khi mở tab.
 */

/** `ChangeAction` phía backend: 1 tạo · 2 sửa · 3 xóa · 4 gửi duyệt · 5 dùng lại · 6 lập bộ tài khoản. */
export const CHANGE_ACTION = {
  CREATE: 1,
  UPDATE: 2,
  DELETE: 3,
  SUBMIT: 4,
  REUSE: 5,
  ACCOUNT: 6,
} as const

/** `undo_status`: 0 chưa hoàn tác · 1 đã hoàn tác · 2 bị chặn (phiếu đã đổi / đã gửi duyệt). */
export const UNDO_STATUS = {
  NONE: 0,
  DONE: 1,
  BLOCKED: 2,
} as const

export interface BotChange {
  id: number
  /** ISO, mốc UTC trần không có `Z` như mọi mốc khác của backend. */
  when: string
  user_id: number
  /** Họ tên nhân sự / email của người bấm (ai-CR-185); thiếu thì hiện #user_id. */
  user_name?: string
  entity: string
  entity_label: string
  entity_id: number
  doc_code: string
  action: number
  action_label: string
  summary: string
  source: number
  source_label: string
  undo_status: number
  undo_status_label: string
  /** Khác 0 = đây là DÒNG NGƯỢC ghi việc hoàn tác dòng gốc `undo_of` — không hoàn tác lại được. */
  undo_of: number
  can_undo: boolean
  /** Lý do nút Hoàn tác tắt; rỗng khi `can_undo`. */
  undo_reason: string
  /** Đường chi tiết v2 của phiếu; rỗng khi không dựng được. */
  url: string
}

/**
 * Ảnh chụp `before` / `after`: chỉ trường đã đổi (`fields`), dòng nếu sửa dòng (`lines`), phần nghỉ phép
 * (`leave`), trạng thái (`status`). Quá trần 64 KB thì backend cắt dòng và cắm `truncated: true`.
 * Tạo → `before = null`; xóa → `after = null`.
 */
export interface ChangeSnapshot {
  fields?: Record<string, unknown>
  lines?: unknown
  leave?: Record<string, unknown>
  status?: unknown
  truncated?: boolean
}

export interface BotChangeDetail extends BotChange {
  before: ChangeSnapshot | null
  after: ChangeSnapshot | null
  undone_at: string
  undone_by: number
}

export interface BotChangeList {
  items: BotChange[]
}

export interface UndoChangeResult {
  /** id DÒNG NGƯỢC vừa ghi. */
  id: number
  undo_of: number
  entity: string
  entity_label: string
  doc_code: string
  action: number
  action_label: string
  summary: string
  url: string
}

/** Trần `limit` của cửa web (`change_service.LIST_MAX`). */
export const BOT_CHANGES_LIMIT_MAX = 200

export const botChangesApi = {
  list: (limit: number, all: boolean) =>
    apiGet<BotChangeList>('/api/assistant/changes', {
      //  Không gửi `all=0` cho gọn URL; backend chỉ đọc `all=1`.
      params: all ? { limit, all: 1 } : { limit },
    }),
  get: (id: number) => apiGet<BotChangeDetail>(`/api/assistant/changes/${id}`),
  /**
   * `_silent`: tắt toast tự động của `httpClient` để hook tự toast đúng `message` trong phong bì
   * (400 hạn / 403 quyền / 404 / 409 phiếu đã đổi) — một lỗi hiện một lần, không hiện đôi.
   */
  undo: (id: number) =>
    apiPost<UndoChangeResult>(`/api/assistant/changes/${id}/undo`, undefined, { _silent: true } as never),
}
