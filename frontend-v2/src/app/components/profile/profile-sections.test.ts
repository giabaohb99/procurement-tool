import { describe, expect, it } from 'vitest'

import {
  DEFAULT_PROFILE_SECTION,
  PROFILE_GROUPS,
  findProfileSection,
  listVisibleProfileGroups,
  resolveProfileSection,
  type ProfileSectionAccess,
} from './profile-sections'

/**
 * Mục của Trang cá nhân (P0 doc 21). Chỗ dễ lủng: link cũ `/me?tab=…` nằm sẵn trong thông
 * báo, tin bot, nút quay lại của phiếu hỗ trợ — đổi bố cục mà một tên cũ rơi về «Thông tin
 * cá nhân» là người dùng bấm link và lạc chỗ, không ai báo lỗi.
 */

const FULL: ProfileSectionAccess = { hasEmployeeProfile: true, canReadTickets: true }
const BARE: ProfileSectionAccess = { hasEmployeeProfile: false, canReadTickets: false }

//  13 tên tab của bố cục cũ (trước P0, 17/10/2026). Không được xóa khỏi danh sách này.
const LEGACY_TABS = [
  'info',
  'work-history',
  'decisions',
  'tasks',
  'notifications',
  'tickets',
  'devices',
  'login-history',
  'telegram',
  'ai-key',
  'bot-memory',
  'bot-changes',
  'appearance',
] as const

describe('resolveProfileSection', () => {
  it('keeps every legacy tab name opening the same section', () => {
    for (const tab of LEGACY_TABS) {
      expect(resolveProfileSection(tab, FULL)).toBe(tab)
    }
  })

  it('opens the new sections by their own names and by the technical alias', () => {
    expect(resolveProfileSection('ai-connect', FULL)).toBe('ai-connect')
    expect(resolveProfileSection('mcp', FULL)).toBe('ai-connect')
    expect(resolveProfileSection('password', BARE)).toBe('password')
  })

  it('falls back to personal info for empty, unknown or hostile values', () => {
    for (const raw of [null, '', '   ', 'khong-co', '__proto__', 'constructor', 'toString', '../admin', 'info?x=1']) {
      expect(resolveProfileSection(raw, FULL)).toBe(DEFAULT_PROFILE_SECTION)
    }
  })

  it('tolerates case and surrounding spaces typed into the address bar', () => {
    expect(resolveProfileSection('  AI-Connect ', FULL)).toBe('ai-connect')
    expect(resolveProfileSection('TICKETS', FULL)).toBe('tickets')
  })

  it('refuses sections the viewer is not allowed to see, even through a direct link', () => {
    expect(resolveProfileSection('work-history', BARE)).toBe('info')
    expect(resolveProfileSection('decisions', BARE)).toBe('info')
    expect(resolveProfileSection('tickets', BARE)).toBe('info')
  })
})

describe('listVisibleProfileGroups', () => {
  it('shows the four groups in order with AI connection first in the AI group', () => {
    const groups = listVisibleProfileGroups(FULL)
    expect(groups.map((g) => g.label)).toEqual(['Hồ sơ', 'Việc của tôi', 'Trợ lý AI của tôi', 'Bảo mật & hiển thị'])
    const ai = groups.find((g) => g.key === 'ai')
    expect(ai?.sections[0].key).toBe('ai-connect')
  })

  it('hides employee-only sections and tickets without dropping the rest of their groups', () => {
    const groups = listVisibleProfileGroups(BARE)
    const keys = groups.flatMap((g) => g.sections.map((s) => s.key))
    expect(keys).not.toContain('work-history')
    expect(keys).not.toContain('decisions')
    expect(keys).not.toContain('tickets')
    expect(groups.find((g) => g.key === 'profile')?.sections.map((s) => s.key)).toEqual(['info'])
    expect(groups).toHaveLength(4)
  })
})

describe('PROFILE_GROUPS', () => {
  it('declares every section exactly once', () => {
    const keys = PROFILE_GROUPS.flatMap((g) => g.sections.map((s) => s.key))
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('finds the group label of each section for the heading above the content', () => {
    expect(findProfileSection('ai-key').group.label).toBe('Trợ lý AI của tôi')
    expect(findProfileSection('ai-key').section.label).toBe('Khóa model AI')
    expect(findProfileSection('appearance').group.label).toBe('Bảo mật & hiển thị')
  })

  it('never uses the technical word MCP in a menu label', () => {
    for (const group of PROFILE_GROUPS) {
      for (const section of group.sections) expect(section.label).not.toMatch(/MCP/i)
    }
  })
})
