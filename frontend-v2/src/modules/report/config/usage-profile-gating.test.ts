import { describe, expect, it } from 'vitest'

import { canAccessRoute } from '@/app/router/module-visibility'
import { appRoutes } from '@/shared/constants/app-routes'

import { reportModule } from '../routes'
import { REPORT_CATALOG } from './report-catalog'

const canAll = () => true
const canAllButSetting = (entity: string) => entity !== 'setting'
const USAGE_KEY = 14
const detail = appRoutes.report.usageProfileDetail(5)

/**
 * Chốt BẢO MẬT (duoc-CR-641): trang hồ sơ MỘT người không có mục menu riêng, nên nó chỉ
 * được gác nếu nằm DƯỚI đường của mục «Hồ sơ cách làm việc» — route không có mục menu
 * khớp thì `canAccessRoute` trả `true` (mở cho mọi người đăng nhập).
 */
describe('usage profile route gating', () => {
  it('registers the list in the catalog under key 14 with entity setting', () => {
    const entry = REPORT_CATALOG.find((r) => r.path === appRoutes.report.usageProfiles)
    expect(entry).toMatchObject({ key: USAGE_KEY, entity: 'setting', overviewKpis: [] })
  })

  it('keeps the detail route under the list path so the menu item gates it', () => {
    expect(detail.startsWith(`${appRoutes.report.usageProfiles}/`)).toBe(true)
    expect(reportModule.routes.map((r) => r.path)).toContain(appRoutes.report.usageProfileDetail(':userId'))
  })

  it('denies the detail page to someone holding the 13 older report keys only', () => {
    const keys = Array.from({ length: 13 }, (_, i) => i + 1)
    expect(canAccessRoute(reportModule, detail, canAll, { reportKeys: keys })).toBe(false)
    expect(canAccessRoute(reportModule, detail, canAll, { reportKeys: [] })).toBe(false)
    expect(canAccessRoute(reportModule, detail, canAll, {})).toBe(false)
  })

  it('allows the detail page with key 14 and setting.read', () => {
    expect(canAccessRoute(reportModule, detail, canAll, { reportKeys: [USAGE_KEY] })).toBe(true)
  })

  it('denies the detail page without setting.read even with key 14', () => {
    expect(canAccessRoute(reportModule, detail, canAllButSetting, { reportKeys: [USAGE_KEY] })).toBe(false)
  })

  it('does not widen another report: key 14 alone does not open a procurement report', () => {
    expect(canAccessRoute(reportModule, appRoutes.report.purchaseReport, canAll, { reportKeys: [USAGE_KEY] })).toBe(false)
  })
})
