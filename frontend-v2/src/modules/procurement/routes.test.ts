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

const PACKAGING_PARENT_LABEL = 'Giá nguyên vật liệu sản xuất'

/** 25/11/2026: cụm là MỘT mục cha có menu con (vẽ như Tra cứu thị trường) — trả các mục con được vẽ. */
function packagingMenu(can: ReturnType<typeof grants>) {
  const parent = visibleNavItems(procurementModule as ErpModule, can).find(
    (item) => item.label === PACKAGING_PARENT_LABEL,
  )
  return (parent?.children ?? []).filter((child) => !child.hidden).map((child) => child.path)
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

  it('marks the root child end:true so it does not light up on the sub-screens', () => {
    const parent = procurementModule.nav.find((item) => item.label === PACKAGING_PARENT_LABEL)
    const root = parent?.children?.find((child) => child.path === appRoutes.procurement.packagingImpact)
    expect(root?.end).toBe(true)
  })

  it('renders as one parent item outside the Mua hàng group, right after it and before Khảo sát', () => {
    const nav = procurementModule.nav
    const parentIndex = nav.findIndex((item) => item.label === PACKAGING_PARENT_LABEL)
    expect(nav[parentIndex]?.group).toBeUndefined()
    expect(nav[parentIndex - 1]?.group).toBe('Mua hàng')
    expect(nav[parentIndex + 1]?.group).toBe('Khảo sát')
  })

  it('registers a route for every menu path', () => {
    const routePaths = procurementModule.routes.map((route) => route.path)
    for (const path of PACKAGING_PATHS) expect(routePaths).toContain(path)
  })
})
