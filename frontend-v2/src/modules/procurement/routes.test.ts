// duoc-CR-784 — ai thấy cụm Giá bao bì trên menu Thu mua, và gõ thẳng URL thì bị chặn ra sao.
import { describe, expect, it } from 'vitest'

import type { ErpModule } from '@/app/router/module-definition'
import { canAccessRoute, visibleNavItems } from '@/app/router/module-visibility'
import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'

import { procurementModule } from './routes'

/** `can` giả lập theo từng cặp "khóa.hành động". */
function grants(...cap: string[]) {
  return (entity: PermissionEntity, action: PermissionAction) => cap.includes(`${entity}.${action}`)
}

const PACKAGING_PATHS = [
  appRoutes.procurement.packagingImpact,
  appRoutes.procurement.packagingProducts,
  appRoutes.procurement.packagingPrices,
  appRoutes.procurement.packagingLastPrices,
  appRoutes.procurement.packagingHistory,
  appRoutes.procurement.packagingQuotes,
  appRoutes.procurement.packagingBoms,
]
/** Báo giá VTBB ẩn khỏi menu (21/11/2026) nhưng đường dẫn vẫn gác quyền như các màn khác. */
const PACKAGING_MENU_PATHS = PACKAGING_PATHS.filter((path) => path !== appRoutes.procurement.packagingQuotes)

function packagingMenu(can: ReturnType<typeof grants>) {
  return visibleNavItems(procurementModule as ErpModule, can)
    .filter((item) => item.group === 'Giá nguyên vật liệu sản xuất' && !item.hidden)
    .map((item) => item.path)
}

describe('Giá bao bì menu (packaging_cost)', () => {
  it('shows the six menu screens to a reader of packaging_cost (Báo giá VTBB is hidden from the menu)', () => {
    expect(packagingMenu(grants('packaging_cost.read'))).toEqual(PACKAGING_MENU_PATHS)
  })

  it('hides them from purchasers without the key — cost of packaging is sensitive', () => {
    expect(
      packagingMenu(grants('purchase_request.read', 'purchase_order.read', 'product.read')),
    ).toEqual([])
  })

  it('blocks typing the URL directly without packaging_cost.read, including deeper paths', () => {
    for (const path of [...PACKAGING_PATHS, `${appRoutes.procurement.packagingPrices}/x`]) {
      expect(
        canAccessRoute(procurementModule as ErpModule, path, grants('purchase_order.read')),
      ).toBe(false)
      expect(
        canAccessRoute(procurementModule as ErpModule, path, grants('packaging_cost.read')),
      ).toBe(true)
    }
  })

  it('marks the root item end:true so it does not light up on the sub-screens', () => {
    const root = procurementModule.nav.find(
      (item) => item.path === appRoutes.procurement.packagingImpact,
    )
    expect(root?.end).toBe(true)
  })

  it('registers a route for every menu path', () => {
    const routePaths = procurementModule.routes.map((route) => route.path)
    for (const path of PACKAGING_PATHS) expect(routePaths).toContain(path)
  })
})
