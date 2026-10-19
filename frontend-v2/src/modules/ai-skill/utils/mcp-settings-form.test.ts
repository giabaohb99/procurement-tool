import { describe, expect, it } from 'vitest'

import type { McpSettings } from '../types/ai-skill'
import { buildPatch, isPatchEmpty, toDraft, validateDraft } from './mcp-settings-form'

/**
 * Bản nháp màn Cấu hình cổng (G7). Hai lỗ dễ lọt nhất: ô bỏ trống thành 0 (`Number('')` = 0, mà 0 ở trần tần suất
 * nghĩa là «không chặn»), và gửi cả bản cấu hình thì đè lên thay đổi người khác vừa lưu ở trường mình không đụng.
 */

function settings(over: Partial<McpSettings> = {}): McpSettings {
  return {
    groups: [
      { key: 'mine', label: 'Của mình', enabled: true, default: true, tools: ['my_tickets'] },
      { key: 'finance', label: 'Công nợ', enabled: false, default: false, tools: ['payable_lookup'] },
    ],
    limits: [
      { key: 'rate_per_ip', label: 'Lượt / phút / IP', value: 300, default: 300, min: 0, max: 20000 },
      { key: 'log_retention_days', label: 'Số ngày giữ', value: 180, default: 180, min: 30, max: 730 },
    ],
    extra_instructions: 'Trả lời ngắn.',
    extra_max_len: 20,
    can_write: true,
    ...over,
  }
}

describe('validateDraft', () => {
  it('rejects an emptied number box instead of reading it as 0 = no limit', () => {
    const s = settings()
    const draft = toDraft(s)
    draft.limits.rate_per_ip = '   '
    expect(validateDraft(s, draft)['limit:rate_per_ip']).toBeDefined()
  })

  it.each(['-1', '1.5', '1e3', '0x10', 'abc', '١٢'])('rejects %s as a limit', (raw) => {
    const s = settings()
    const draft = toDraft(s)
    draft.limits.rate_per_ip = raw
    expect(validateDraft(s, draft)['limit:rate_per_ip']).toBeDefined()
  })

  it('accepts the range ends and rejects one past them', () => {
    const s = settings()
    const draft = toDraft(s)
    draft.limits.log_retention_days = '30'
    draft.limits.rate_per_ip = '0'
    expect(validateDraft(s, draft)).toEqual({})
    draft.limits.log_retention_days = '29'
    draft.limits.rate_per_ip = '20001'
    expect(Object.keys(validateDraft(s, draft)).sort()).toEqual(['limit:log_retention_days', 'limit:rate_per_ip'])
  })

  it('counts the instruction length after trimming, like the server does', () => {
    const s = settings()
    const draft = toDraft(s)
    draft.extra = `   ${'a'.repeat(20)}   `
    expect(validateDraft(s, draft).extra).toBeUndefined()
    draft.extra = 'a'.repeat(21)
    expect(validateDraft(s, draft).extra).toBeDefined()
  })
})

describe('buildPatch', () => {
  it('sends nothing when nothing changed, even with padding around a number', () => {
    const s = settings()
    const draft = toDraft(s)
    draft.limits.rate_per_ip = ' 300 '
    draft.extra = ' Trả lời ngắn. '
    expect(isPatchEmpty(buildPatch(s, draft))).toBe(true)
  })

  it('sends only the changed group, limit and instruction', () => {
    const s = settings()
    const draft = toDraft(s)
    draft.groups.finance = true
    draft.limits.rate_per_ip = '0'
    draft.extra = ''
    expect(buildPatch(s, draft)).toEqual({ groups: { finance: true }, rate_per_ip: 0, extra_instructions: '' })
  })

  it('ignores a group the server no longer lists', () => {
    const s = settings()
    const draft = toDraft(s)
    draft.groups.removed_group = true
    expect(isPatchEmpty(buildPatch(s, draft))).toBe(true)
  })
})
