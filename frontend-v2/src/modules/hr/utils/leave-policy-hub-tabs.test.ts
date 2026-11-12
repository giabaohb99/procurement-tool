import { describe, expect, it } from 'vitest'

import { canAccessRoute, visibleNavItems } from '@/app/router/module-visibility'
import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'
import { hrModule } from '../routes'
import {
  buildLeavePolicyHubHref,
  getVisibleLeavePolicyHubTabs,
  LEAVE_POLICY_HUB_TITLE,
  resolveLeavePolicyHubTab,
} from './leave-policy-hub-tabs'

const ACTIONS: PermissionAction[] = ['read', 'create', 'write', 'delete']

function makeCan(grants: string[]) {
  const set = new Set(grants)
  return (entity: PermissionEntity, action: PermissionAction) => set.has(`${entity}.${action}`)
}

/** Mọi tổ hợp quyền trên hai khóa của màn (2^8 = 256 tài khoản giả). */
function everyGrantCombination(): string[][] {
  const atoms = (['leave_balance', 'leave_type'] as const).flatMap((e) => ACTIONS.map((a) => `${e}.${a}`))
  const combos: string[][] = []
  for (let mask = 0; mask < 1 << atoms.length; mask++) combos.push(atoms.filter((_, i) => mask & (1 << i)))
  return combos
}

describe('leave policy hub tabs (duoc-CR-750)', () => {
  it('keeps the menu/route fence and the tab rule identical for every permission combination', () => {
    //  Lệch nhau là một trong hai lỗi im lặng: vào được màn mà không có tab nào (trang trắng), hoặc thấy tab mà
    //  gõ URL bị chặn. Gác điều hướng mặc định MỞ nên mục menu chính là hàng rào duy nhất phía giao diện.
    for (const grants of everyGrantCombination()) {
      const can = makeCan(grants)
      const routeOpen = canAccessRoute(hrModule, appRoutes.hr.leavePolicyAssignments, can)
      expect({ grants, routeOpen }).toEqual({ grants, routeOpen: getVisibleLeavePolicyHubTabs(can).length > 0 })
    }
  })

  it('the menu entry is labelled like the page title and lives in the Thiết lập cluster, not under Nghỉ phép (duoc-CR-754)', () => {
    const can = makeCan(['leave_balance.read', 'leave_balance.write', 'leave_type.write', 'holiday.write'])
    const items = visibleNavItems(hrModule, can)
    const setupLabels = items.find((i) => i.label === 'Thiết lập')?.children?.map((c) => c.label) ?? []
    expect(setupLabels[0]).toBe(LEAVE_POLICY_HUB_TITLE)
    const leaveLabels = items.find((i) => i.label === 'Nghỉ phép')?.children?.map((c) => c.label) ?? []
    expect(leaveLabels).toEqual(['Quỹ phép năm'])
    //  Mục cũ "Phân bổ chính sách" không còn đứng song song.
    expect([...setupLabels, ...leaveLabels]).not.toContain('Phân bổ chính sách')
  })

  it('read-only rights (the seed gives leave_balance.read to everyone) open no tab', () => {
    const can = makeCan(['leave_balance.read', 'leave_type.read'])
    expect(getVisibleLeavePolicyHubTabs(can)).toEqual([])
    expect(resolveLeavePolicyHubTab('assignments', can)).toBeNull()
    expect(resolveLeavePolicyHubTab(null, can)).toBeNull()
  })

  it('picks the URL tab only when allowed, otherwise the first allowed tab', () => {
    const both = makeCan(['leave_balance.write', 'leave_type.write'])
    expect(resolveLeavePolicyHubTab(null, both)).toBe('assignments')
    expect(resolveLeavePolicyHubTab('', both)).toBe('assignments')
    expect(resolveLeavePolicyHubTab('policies', both)).toBe('policies')
    expect(resolveLeavePolicyHubTab('POLICIES', both)).toBe('assignments')
    expect(resolveLeavePolicyHubTab('constructor', both)).toBe('assignments')

    const policyOnly = makeCan(['leave_type.write'])
    expect(resolveLeavePolicyHubTab(null, policyOnly)).toBe('policies')
    expect(resolveLeavePolicyHubTab('assignments', policyOnly)).toBe('policies')

    const assignOnly = makeCan(['leave_balance.write'])
    expect(resolveLeavePolicyHubTab('policies', assignOnly)).toBe('assignments')
  })

  it('builds the tab link on the old assignment path, overriding any tab already in the extra params', () => {
    expect(buildLeavePolicyHubHref('policies')).toBe('/hr/leave-policy-assignments?tab=policies')
    expect(buildLeavePolicyHubHref('assignments', new URLSearchParams('tab=policies&q=a%26b'))).toBe(
      '/hr/leave-policy-assignments?tab=assignments&q=a%26b',
    )
    expect(buildLeavePolicyHubHref('policies', new URLSearchParams(''))).toBe('/hr/leave-policy-assignments?tab=policies')
  })
})
