import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '@/core/api'

/**
 * «Bot đang nhớ gì về tôi» (ai-CR-138, phase 13.4). Mọi cửa lấy người dùng từ phiên đăng nhập — không có tham số chọn
 * người khác, không có biến thể cho quản trị.
 */
export type MemorySectionKey = 'ban_than' | 'so_thich' | 'cach_lam_viec' | 'da_chot'

export interface MemoryLine {
  /** Nguyên văn dòng trong sổ — dùng làm khóa khi sửa / xóa (đổi ở tab khác thì backend trả 409). */
  text: string
  /** Dòng đã bỏ đuôi «(tự rút)» và đuôi hạn. */
  fact: string
  auto: boolean
  until: string | null
}

export interface MemorySection {
  key: MemorySectionKey
  label: string
  lines: MemoryLine[]
}

export interface MemoryWatching {
  id: number
  fact: string
  section: MemorySectionKey | ''
  hits: number
  days: number
  need_hits: number
  need_days: number
  confidence: number
  last_seen_at: string | null
}

export interface MemoryNote {
  id: number
  title: string
  chars: number
  created_at: string | null
}

export interface MemoryHabit {
  type: string
  label: string
  value: string
  count: number
  total: number
}

export interface MemorySuggestion {
  sub: string
  label: string
  weekday: number
  weeks: number
  text: string
}

export interface BotMemory {
  sections: MemorySection[]
  chars: number
  max: number
  watching: MemoryWatching[]
  notes: MemoryNote[]
  habits: MemoryHabit[]
  suggestions: MemorySuggestion[]
  auto_enabled: boolean
}

export interface MemoryLineInput {
  section: MemorySectionKey
  text: string
  until?: string | null
}

export interface MemoryLineEdit {
  section: MemorySectionKey
  old: string
  text?: string
}

export const botMemoryApi = {
  get: () => apiGet<BotMemory>('/api/agent-hub/me/memory'),
  addLine: (body: MemoryLineInput) => apiPost<BotMemory>('/api/agent-hub/me/memory/lines', body),
  editLine: (body: MemoryLineEdit) => apiPatch<BotMemory>('/api/agent-hub/me/memory/lines', body),
  deleteLine: (body: MemoryLineEdit) => apiPost<BotMemory>('/api/agent-hub/me/memory/lines/delete', body),
  dropWatching: (id: number) => apiDelete<BotMemory>(`/api/agent-hub/me/memory/watching/${id}`),
  deleteNote: (id: number) => apiDelete<BotMemory>(`/api/agent-hub/me/memory/notes/${id}`),
  wipe: () => apiDelete<BotMemory>('/api/agent-hub/me/memory'),
}

/** Bản tin bot tự gửi (ai-CR-140). `kind` 1 = bản tin sáng · 2 = bản tin chủ đề. `days` mặt nạ thứ (thứ hai = 1 … chủ
 *  nhật = 64). `implicit` = bản tin sáng ngầm của người đã nối Google mà chưa tự đặt (id 0). */
export interface BriefItem {
  id: number
  kind: 1 | 2
  enabled: boolean
  hour: number
  minute: number
  days: number
  topic: string
  sub_code: string
  implicit: boolean
  label: string
  when: string
}

export interface BriefList {
  items: BriefItem[]
}

export interface BriefTopicInput {
  question: string
  hour: number
  minute: number
  days: number
  sub_code?: string
}

export const botBriefApi = {
  list: () => apiGet<BriefList>('/api/agent-hub/me/briefs'),
  setDaily: (body: { enabled: boolean; hour?: number; minute?: number; days?: number }) =>
    apiPut<BriefList>('/api/agent-hub/me/briefs/daily', body),
  addTopic: (body: BriefTopicInput) => apiPost<BriefList>('/api/agent-hub/me/briefs/topics', body),
  toggle: ({ id, enabled }: { id: number; enabled: boolean }) =>
    apiPatch<BriefList>(`/api/agent-hub/me/briefs/${id}`, { enabled }),
  remove: (id: number) => apiDelete<BriefList>(`/api/agent-hub/me/briefs/${id}`),
}
