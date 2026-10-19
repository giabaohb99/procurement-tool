import type { McpSettings, McpSettingsPatch } from '../types/ai-skill'

/**
 * Bản nháp của màn Cấu hình cổng (G7, doc/agent-hub/06 §7.3). Ô số giữ CHUỖI người dùng gõ để kiểm được cả ô rỗng,
 * số lẻ, số âm trước khi gửi — máy chủ cũng chặn (sai một trường là 400, không lưu gì), nhưng báo đúng ô ngay tại chỗ
 * thì người dùng không phải đoán trường nào làm hỏng cả lượt lưu.
 */
export interface McpSettingsDraft {
  groups: Record<string, boolean>
  limits: Record<string, string>
  extra: string
}

export function toDraft(settings: McpSettings): McpSettingsDraft {
  return {
    groups: Object.fromEntries(settings.groups.map((g) => [g.key, g.enabled])),
    limits: Object.fromEntries(settings.limits.map((l) => [l.key, String(l.value)])),
    extra: settings.extra_instructions,
  }
}

const WHOLE_NUMBER_RE = /^\d+$/

/** Lỗi theo khóa ô (`limit:<khóa>` hoặc `extra`); rỗng = hợp lệ. */
export function validateDraft(settings: McpSettings, draft: McpSettingsDraft): Record<string, string> {
  const errors: Record<string, string> = {}
  for (const limit of settings.limits) {
    const raw = (draft.limits[limit.key] ?? '').trim()
    //  `Number('')` = 0 và `Number('1e3')` = 1000 — chỉ nhận chuỗi toàn chữ số, kẻo ô bỏ trống thành 0 = «không chặn».
    if (!WHOLE_NUMBER_RE.test(raw)) {
      errors[`limit:${limit.key}`] = 'Nhập số nguyên không âm.'
      continue
    }
    const value = Number(raw)
    if (value < limit.min || value > limit.max) {
      errors[`limit:${limit.key}`] = `Chỉ nhận từ ${limit.min} tới ${limit.max}.`
    }
  }
  if (draft.extra.trim().length > settings.extra_max_len) {
    errors.extra = `Tối đa ${settings.extra_max_len} ký tự.`
  }
  return errors
}

/**
 * Chỉ gửi phần ĐÃ ĐỔI (máy chủ nhận lưu một phần, giữ phần cũ). Gửi cả bản thì một quản trị lưu đè lên thay đổi người
 * kia vừa lưu ở trường mình không đụng tới. Gọi sau `validateDraft` rỗng lỗi.
 */
export function buildPatch(settings: McpSettings, draft: McpSettingsDraft): McpSettingsPatch {
  const patch: McpSettingsPatch = {}
  const groups: Record<string, boolean> = {}
  for (const group of settings.groups) {
    const next = draft.groups[group.key]
    if (next !== undefined && next !== group.enabled) groups[group.key] = next
  }
  if (Object.keys(groups).length > 0) patch.groups = groups
  for (const limit of settings.limits) {
    const value = Number((draft.limits[limit.key] ?? '').trim())
    if (value !== limit.value) patch[limit.key] = value
  }
  const extra = draft.extra.trim()
  if (extra !== settings.extra_instructions) patch.extra_instructions = extra
  return patch
}

export function isPatchEmpty(patch: McpSettingsPatch): boolean {
  return Object.keys(patch).length === 0
}
