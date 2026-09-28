import { describe, expect, it } from 'vitest'

import type { ModuleNavItem } from '@/app/router/module-definition'
import { allModules } from '@/app/router/module-registry'
import { appRoutes } from '@/shared/constants/app-routes'

import { reportModule } from '../routes'
import { REPORT_CATALOG } from './report-catalog'

/** Dàn phẳng menu (kể cả mục con) của mọi phân hệ trừ Báo cáo. */
function flattenSourceNav(): ModuleNavItem[] {
  const walk = (items: ModuleNavItem[]): ModuleNavItem[] =>
    items.flatMap((i) => [i, ...walk(i.children ?? [])])
  return allModules.filter((m) => m.id !== 'report').flatMap((m) => walk(m.nav))
}

describe('REPORT_CATALOG', () => {
  it('each report path lives under /report and is unique', () => {
    const paths = REPORT_CATALOG.map((r) => r.path)
    expect(new Set(paths).size).toBe(paths.length)
    for (const p of paths) expect(p.startsWith(`${appRoutes.report.root}/`)).toBe(true)
  })

  //  Cùng một trang gắn hai đường: khóa quyền bên Báo cáo lệch khóa bên phân hệ
  //  gốc là người bị chặn ở Thu mua vẫn vào được qua cửa Báo cáo (hoặc ngược lại).
  it('permission key matches the source module menu item for the same page', () => {
    const sourceNav = flattenSourceNav()
    for (const r of REPORT_CATALOG) {
      const src = sourceNav.find((i) => i.path === r.sourcePath && !i.crossModule)
      expect(src, `thiếu mục menu gốc cho ${r.sourcePath}`).toBeDefined()
      expect(src?.entity).toBe(r.entity)
    }
  })

  it('every report has a menu item and a route in the Report module', () => {
    const navPaths = reportModule.nav.map((i) => i.path)
    const routePaths = reportModule.routes.map((r) => r.path)
    for (const r of REPORT_CATALOG) {
      expect(navPaths).toContain(r.path)
      expect(routePaths).toContain(r.path)
    }
  })

  it('overview is gated by the union of every report key, so no report leaves it hidden', () => {
    const overview = reportModule.nav.find((i) => i.path === appRoutes.report.root)
    expect(new Set(overview?.entities)).toEqual(new Set(REPORT_CATALOG.map((r) => r.entity)))
  })

  it('every loader resolves to a real component', async () => {
    for (const r of REPORT_CATALOG) expect(typeof (await r.load())).toBe('function')
  })
})
