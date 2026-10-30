import { isValidElement } from 'react'
import { describe, expect, it } from 'vitest'

import { canOpenModule, visibleNavItems } from '@/app/router/module-visibility'
import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'
import { aiSkillModule } from './routes'

/**
 * Thẻ phân hệ Kho skill AI hiện khi đọc được `ai_skill` HOẶC `ai_mcp_key_admin` (Agent 1 chốt, K5). Phân hệ không
 * khai `entity` ở cấp phân hệ nên luật này nằm hết ở các mục menu — sửa nhầm một mục là thẻ mở cho người ngoài, hoặc
 * người quản lý khóa vào phân hệ không thấy gì.
 */

function canFrom(grants: Partial<Record<PermissionEntity, PermissionAction[]>>) {
  return (entity: PermissionEntity, action: PermissionAction) => grants[entity]?.includes(action) ?? false
}

describe('aiSkillModule visibility', () => {
  it('stays closed to someone with neither key', () => {
    expect(canOpenModule(aiSkillModule, canFrom({ assistant: ['read'] }))).toBe(false)
  })

  it('opens for a skill editor and shows the skill screens, not the key admin', () => {
    const can = canFrom({ ai_skill: ['read', 'write'] })
    expect(canOpenModule(aiSkillModule, can)).toBe(true)
    const labels = visibleNavItems(aiSkillModule, can).map((i) => i.label)
    expect(labels).toContain('Bộ skill')
    expect(labels).toContain('Nhật ký sử dụng')
    expect(labels).not.toContain('Khóa nhân sự')
  })

  it('opens for a key admin who cannot read skills, with keys and the log only', () => {
    const can = canFrom({ ai_mcp_key_admin: ['read'] })
    expect(canOpenModule(aiSkillModule, can)).toBe(true)
    //  bao-CR-635: "Ứng dụng AI đã kết nối" gác theo hai khóa của phân hệ như Cấu hình, trang tự kiểm `agent_group`.
    expect(visibleNavItems(aiSkillModule, can).map((i) => i.label)).toEqual([
      'Tổng quan', 'Khóa nhân sự', 'Ứng dụng AI đã kết nối', 'Nhật ký sử dụng', 'Cấu hình',
    ])
  })

  it('keeps the intro hidden for now: no menu item, and the old link sends people to the overview', () => {
    //  26/10/2026: mục Giới thiệu tạm ẩn để làm lại — link cũ phải về Tổng quan, không ra trang trắng hay trang cũ.
    const all = visibleNavItems(aiSkillModule, canFrom({ ai_skill: ['read', 'write'], ai_mcp_key_admin: ['read'] }))
    expect(all.map((i) => i.path)).not.toContain(appRoutes.aiSkill.intro)
    const intro = aiSkillModule.routes.find((r) => r.path === appRoutes.aiSkill.intro)
    expect(intro?.lazy).toBeUndefined()
    expect(isValidElement(intro?.element) && (intro.element.props as { to?: string }).to).toBe(appRoutes.aiSkill.overview)
  })

  it('does not open the module to a bot manager who holds neither skill key', () => {
    expect(canOpenModule(aiSkillModule, canFrom({ agent_group: ['read'] }))).toBe(false)
  })

  it('shows the gateway settings to anyone inside the module, the page itself checks the bot-manager right', () => {
    //  G7 (ai-CR-216) đòi `agent_group`, không đòi quyền sửa skill — gác mục bằng `ai_skill` manage như bản K5 thì
    //  người quản lý bot chỉ đọc kho skill không tìm thấy màn cấu hình cổng.
    const reader = visibleNavItems(aiSkillModule, canFrom({ ai_skill: ['read'] })).map((i) => i.label)
    expect(reader).toContain('Cấu hình')
  })
})
