import { render, screen } from '@testing-library/react'
import { isValidElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ModuleSidebar } from '@/app/layouts/module-sidebar'
import { allModules, moduleRegistry } from '@/app/router/module-registry'
import { findModuleByPath } from '@/app/router/use-active-module'
import {
  canAccessRoute,
  canOpenModule,
  firstAccessibleNavPath,
  visibleNavItems,
} from '@/app/router/module-visibility'
import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'
import { SidebarProvider } from '@/shared/ui/sidebar'
import { aiModule } from './routes'

/**
 * Phân hệ AI (bao-CR-696) gộp Trợ lý AI + Kho skill AI. Ba lời hứa khi gộp, sai cái nào cũng im lặng:
 * 1. Quyền từng mục GIỮ NGUYÊN như hai phân hệ cũ — gộp mà nới một mục là mở màn cho người ngoài.
 * 2. Route cũ vẫn mở — link trong thông báo / dấu trang / bài HDSD trỏ vào `/assistant/...` và `/ai-skill/...`.
 * 3. Bot Telegram thu vào mục sổ xuống, ĐÓNG sẵn.
 */

type Grants = Partial<Record<PermissionEntity, PermissionAction[]>>

function canFrom(grants: Grants) {
  return (entity: PermissionEntity, action: PermissionAction) => grants[entity]?.includes(action) ?? false
}

/** Nhãn menu như người dùng thấy: mục ẩn bỏ đi, mục cha kèm mục con còn hiện. */
function menuOf(grants: Grants): string[] {
  return visibleNavItems(aiModule, canFrom(grants))
    .filter((i) => !i.hidden)
    .flatMap((i) => (i.children?.length ? [i.label, ...i.children.map((c) => `${i.label} > ${c.label}`)] : [i.label]))
}

describe('aiModule menu by permission', () => {
  it('stays closed to someone with none of the four keys', () => {
    expect(canOpenModule(aiModule, canFrom({}))).toBe(false)
    expect(canOpenModule(aiModule, canFrom({ purchase_request: ['read', 'write'] }))).toBe(false)
  })

  it('gives a leadership user (assistant only) the chat and the Telegram groups, nothing from the skill store', () => {
    expect(menuOf({ assistant: ['read'] })).toEqual(['Trợ lý AI', 'Bot Telegram', 'Bot Telegram > Nhóm chat'])
  })

  it('gives a skill editor the skill store, monitoring and settings, but not connections or the advanced screen', () => {
    expect(menuOf({ ai_skill: ['read', 'write'] })).toEqual([
      'Bộ skill',
      'Tổng quan',
      'Nhật ký sử dụng',
      'Cấu hình chung',
    ])
  })

  it('gives a key admin who cannot read skills the connections screen, monitoring and settings', () => {
    expect(menuOf({ ai_mcp_key_admin: ['read'] })).toEqual([
      'Kết nối',
      'Tổng quan',
      'Nhật ký sử dụng',
      'Cấu hình chung',
    ])
  })

  it('keeps the advanced screen (OAuth app registrations) for bot managers only', () => {
    //  Trước bao-CR-696 mục này hiện cho mọi người trong Kho skill rồi trang tự báo thiếu quyền; nay chỉ quản trị.
    expect(menuOf({ ai_skill: ['read', 'write'], ai_mcp_key_admin: ['read', 'create', 'delete'] })).not.toContain(
      'Nâng cao',
    )
    expect(menuOf({ agent_group: ['read'] })).toEqual(['Bot Telegram', 'Bot Telegram > Người dùng bot', 'Nâng cao'])
  })

  it('shows the full menu in the agreed order to someone holding every key', () => {
    const all: Grants = {
      assistant: ['read'],
      ai_skill: ['read', 'write'],
      ai_mcp_key_admin: ['read'],
      agent_group: ['read'],
    }
    expect(menuOf(all)).toEqual([
      'Trợ lý AI',
      'Kết nối',
      'Bộ skill',
      'Tổng quan',
      'Nhật ký sử dụng',
      'Bot Telegram',
      'Bot Telegram > Nhóm chat',
      'Bot Telegram > Người dùng bot',
      'Cấu hình chung',
      'Nâng cao',
    ])
    const groups = visibleNavItems(aiModule, canFrom(all))
      .filter((i) => !i.hidden)
      .map((i) => i.group ?? '')
    expect([...new Set(groups)]).toEqual(['', 'Kho skill', 'Giám sát', 'Cấu hình'])
  })
})

describe('aiModule keeps the old routes', () => {
  const OLD_ROUTES = [
    appRoutes.assistant.root,
    appRoutes.assistant.groups,
    appRoutes.assistant.botUsers,
    appRoutes.assistant.group(':id'),
    appRoutes.aiSkill.root,
    appRoutes.aiSkill.overview,
    appRoutes.aiSkill.setDetail(':id'),
    appRoutes.aiSkill.skillEditor(':id'),
    appRoutes.aiSkill.keys,
    appRoutes.aiSkill.oauthClients,
    appRoutes.aiSkill.logs,
    appRoutes.aiSkill.settings,
    appRoutes.aiSkill.intro,
  ]

  it('registers every route the two old modules had, once', () => {
    const paths = aiModule.routes.map((r) => r.path)
    for (const path of OLD_ROUTES) expect(paths.filter((p) => p === path), path).toHaveLength(1)
    expect(paths).toHaveLength(OLD_ROUTES.length)
  })

  it('resolves both old prefixes to the AI module, and no other module claims them', () => {
    for (const path of ['/assistant', '/assistant/groups/7', '/ai-skill', '/ai-skill/keys', '/ai-skill/skills/3']) {
      expect(findModuleByPath(path)?.id, path).toBe('ai')
    }
    //  Tiền tố gần giống không được bắt nhầm (`/ai-skillx` không phải `/ai-skill`).
    expect(findModuleByPath('/ai-skillx')?.id).not.toBe('ai')
    expect(allModules.map((m) => m.id)).not.toContain('assistant')
    expect(allModules.map((m) => m.id)).not.toContain('ai-skill')
    expect(moduleRegistry.filter((m) => m.id === 'ai')).toHaveLength(1)
  })

  it('keeps the intro hidden: no menu item, and the old link sends people to the overview', () => {
    const everything = canFrom({ assistant: ['read'], ai_skill: ['read'], ai_mcp_key_admin: ['read'], agent_group: ['read'] })
    expect(visibleNavItems(aiModule, everything).map((i) => i.path)).not.toContain(appRoutes.aiSkill.intro)
    const intro = aiModule.routes.find((r) => r.path === appRoutes.aiSkill.intro)
    expect(intro?.lazy).toBeUndefined()
    expect(isValidElement(intro?.element) && (intro.element.props as { to?: string }).to).toBe(appRoutes.aiSkill.overview)
  })

  it('still blocks a typed URL per screen, with the same key as before the merge', () => {
    const leader = canFrom({ assistant: ['read'] })
    expect(canAccessRoute(aiModule, '/assistant', leader)).toBe(true)
    expect(canAccessRoute(aiModule, '/assistant/groups/5', leader)).toBe(true)
    expect(canAccessRoute(aiModule, '/assistant/bot-users', leader)).toBe(false)
    expect(canAccessRoute(aiModule, '/ai-skill/sets/5', leader)).toBe(false)
    expect(canAccessRoute(aiModule, '/ai-skill/keys', leader)).toBe(false)

    const editor = canFrom({ ai_skill: ['read', 'write'] })
    expect(canAccessRoute(aiModule, '/ai-skill/skills/9', editor)).toBe(true)
    expect(canAccessRoute(aiModule, '/assistant', editor)).toBe(false)
    expect(canAccessRoute(aiModule, '/ai-skill/oauth-clients', editor)).toBe(false)
  })

  it('never lands anyone on a screen they cannot open when the card sends them to the chat they lack', () => {
    //  Bấm thẻ AI là vào `/assistant`; thiếu `assistant` thì `ModuleLayout` đưa sang `firstAccessibleNavPath`. Mục cha
    //  "Bot Telegram" từng trỏ Nhóm chat — người chỉ quản lý bot đáp xuống trang 403.
    const keys: PermissionEntity[] = ['assistant', 'ai_skill', 'ai_mcp_key_admin', 'agent_group']
    for (let mask = 1; mask < 1 << keys.length; mask++) {
      const grants: Grants = {}
      keys.forEach((k, i) => {
        if (mask & (1 << i)) grants[k] = ['read']
      })
      const can = canFrom(grants)
      if (canAccessRoute(aiModule, aiModule.path, can)) continue
      const target = firstAccessibleNavPath(aiModule, can)
      expect(target, JSON.stringify(grants)).not.toBeNull()
      expect(canAccessRoute(aiModule, target ?? '', can), `${JSON.stringify(grants)} -> ${target}`).toBe(true)
    }
  })
})

//  Sidebar thật, quyền đổi theo từng bài — để thấy mục Bot Telegram đóng / mở và mục thiếu quyền biến mất.
const permissionState = vi.hoisted(() => ({ grants: {} as Partial<Record<string, string[]>> }))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => permissionState.grants[entity]?.includes(action) ?? false,
    canAny: () => true,
  }),
  useNavContext: () => ({}),
}))

function renderSidebarAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <SidebarProvider>
        <ModuleSidebar module={aiModule} onResizeWidth={vi.fn()} />
      </SidebarProvider>
    </MemoryRouter>,
  )
}

describe('aiModule sidebar', () => {
  beforeEach(() => {
    permissionState.grants = {
      assistant: ['read'],
      ai_skill: ['read'],
      ai_mcp_key_admin: ['read'],
      agent_group: ['read'],
    }
  })

  it('keeps the Telegram bot group folded away on other screens', () => {
    renderSidebarAt('/ai-skill/keys')
    expect(screen.getByText('Bot Telegram')).toBeInTheDocument()
    expect(screen.queryByText('Nhóm chat')).not.toBeInTheDocument()
    expect(screen.queryByText('Người dùng bot')).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: /kết nối/i })).toHaveAttribute('aria-current', 'page')
  })

  it('unfolds the Telegram bot group when standing on one of its screens', () => {
    renderSidebarAt('/assistant/groups/12')
    expect(screen.getByText('Nhóm chat')).toBeInTheDocument()
    expect(screen.getByText('Người dùng bot')).toBeInTheDocument()
  })

  it('shows group headings in order and hides what the user cannot open', () => {
    permissionState.grants = { ai_skill: ['read'] }
    renderSidebarAt('/ai-skill')
    expect(screen.getByText('Kho skill')).toBeInTheDocument()
    expect(screen.getByText('Giám sát')).toBeInTheDocument()
    expect(screen.queryByText('Trợ lý AI')).not.toBeInTheDocument()
    expect(screen.queryByText('Kết nối')).not.toBeInTheDocument()
    expect(screen.queryByText('Bot Telegram')).not.toBeInTheDocument()
    expect(screen.queryByText('Nâng cao')).not.toBeInTheDocument()
  })
})
