// duoc-CR-784 — ai thấy cụm Giá bao bì trên menu Thu mua, và gõ thẳng URL thì bị chặn ra sao.
// bao-CR-792 — khóa chung `packaging_cost` nghỉ hẳn: mỗi màn một khóa, mục cha hiện theo mục con.
import { describe, expect, it } from 'vitest'

import type { ErpModule } from '@/app/router/module-definition'
import {
  canAccessRoute,
  canOpenModule,
  firstAccessibleNavPath,
  navItemLandingPath,
  visibleNavItems,
} from '@/app/router/module-visibility'
import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'

import { procurementModule } from './routes'

/** `can` giả lập theo từng cặp "khóa.hành động". */
function grants(...cap: string[]) {
  return (entity: PermissionEntity, action: PermissionAction) => cap.includes(`${entity}.${action}`)
}

/** Hợp đồng bao-CR-792: đường của từng màn → khóa quyền của màn đó (Báo giá VTBB dùng chung khóa Bảng giá VTBB). */
const PACKAGING_SCREEN_KEYS: [path: string, entity: PermissionEntity][] = [
  [appRoutes.procurement.packagingImpact, 'packaging_impact'],
  [appRoutes.procurement.packagingProducts, 'packaging_product_summary'],
  [appRoutes.procurement.packagingPrices, 'packaging_price_list'],
  //  duoc-CR-798: Bảng giá nguyên liệu đứng ngay dưới Bảng giá VTBB, cùng khóa xem bảng giá.
  [appRoutes.procurement.packagingMaterialPrices, 'packaging_price_list'],
  [appRoutes.procurement.packagingLastPrices, 'packaging_last_price'],
  [appRoutes.procurement.packagingHistory, 'packaging_history'],
  [appRoutes.procurement.packagingQuotes, 'packaging_price_list'],
  [appRoutes.procurement.packagingBoms, 'packaging_bom'],
]
const PACKAGING_PATHS = PACKAGING_SCREEN_KEYS.map(([path]) => path)
/** Báo giá VTBB ẩn khỏi menu (21/11/2026) nhưng đường dẫn vẫn gác quyền như các màn khác. */
const PACKAGING_MENU_PATHS = PACKAGING_PATHS.filter((path) => path !== appRoutes.procurement.packagingQuotes)
const ALL_PACKAGING_READS = [...new Set(PACKAGING_SCREEN_KEYS.map(([, entity]) => `${entity}.read`))]

const PACKAGING_PARENT_LABEL = 'Giá nguyên vật liệu sản xuất'

function packagingParent(can: ReturnType<typeof grants>) {
  return visibleNavItems(procurementModule as ErpModule, can).find(
    (item) => item.label === PACKAGING_PARENT_LABEL,
  )
}

/** 25/11/2026: cụm là MỘT mục cha có menu con (vẽ như Tra cứu thị trường) — trả các mục con được vẽ. */
function packagingMenu(can: ReturnType<typeof grants>) {
  return (packagingParent(can)?.children ?? []).filter((child) => !child.hidden).map((child) => child.path)
}

describe('Giá bao bì menu (bao-CR-792: one key per screen)', () => {
  it('shows the six menu screens to someone who reads all six keys (Báo giá VTBB is hidden from the menu)', () => {
    expect(packagingMenu(grants(...ALL_PACKAGING_READS))).toEqual(PACKAGING_MENU_PATHS)
  })

  it('hides them from purchasers without any key — cost of packaging is sensitive', () => {
    const can = grants('purchase_request.read', 'purchase_order.read', 'product.read')
    expect(packagingParent(can)).toBeUndefined()
    expect(packagingMenu(can)).toEqual([])
  })

  it('no longer opens anything for the retired packaging_cost key', () => {
    const can = grants('packaging_cost.read')
    expect(packagingParent(can)).toBeUndefined()
    for (const path of PACKAGING_PATHS) {
      expect(canAccessRoute(procurementModule as ErpModule, path, can)).toBe(false)
    }
  })

  it('gates every screen with its own key: one key opens exactly its screens, on the menu and by URL', () => {
    for (const entity of new Set(PACKAGING_SCREEN_KEYS.map(([, key]) => key))) {
      const can = grants(`${entity}.read`)
      const ownPaths = PACKAGING_SCREEN_KEYS.filter(([, key]) => key === entity).map(([path]) => path)
      expect(packagingMenu(can), entity).toEqual(PACKAGING_MENU_PATHS.filter((path) => ownPaths.includes(path)))
      for (const path of PACKAGING_PATHS) {
        expect(canAccessRoute(procurementModule as ErpModule, path, can), `${entity} → ${path}`).toBe(
          ownPaths.includes(path),
        )
      }
    }
  })

  it('shows the parent as soon as ONE child is readable, listing only that child', () => {
    const can = grants('packaging_history.read')
    expect(packagingParent(can)?.label).toBe(PACKAGING_PARENT_LABEL)
    expect(packagingMenu(can)).toEqual([appRoutes.procurement.packagingHistory])
  })

  it('sends a click on the parent to the first child the user may read, not to the Tác động screen', () => {
    //  Menu trái đi tới mục con ĐẦU của danh sách đã lọc quyền; breadcrumb dùng `navItemLandingPath`.
    const can = grants('packaging_last_price.read', 'packaging_bom.read')
    const parent = packagingParent(can)
    expect(parent?.children?.[0]?.path).toBe(appRoutes.procurement.packagingLastPrices)
    const declared = procurementModule.nav.find((item) => item.label === PACKAGING_PARENT_LABEL)!
    expect(navItemLandingPath(declared, can)).toBe(appRoutes.procurement.packagingLastPrices)
    //  Có quyền màn Tác động (đường gốc của cụm) thì vẫn về đó như cũ.
    expect(navItemLandingPath(declared, grants(...ALL_PACKAGING_READS))).toBe(appRoutes.procurement.packagingImpact)
  })

  it('lets someone holding a single packaging key into Thu mua and lands them on their own screen', () => {
    //  Không đọc được Tổng quan → `ModuleLayout` đẩy tới màn đầu tiên xem được: phải là màn của khóa đang giữ, không
    //  phải màn Tác động giá (đường của mục cha) — ở đó họ gặp trang cấm.
    for (const [path, entity] of PACKAGING_SCREEN_KEYS) {
      if (path === appRoutes.procurement.packagingQuotes) continue
      //  Bảng giá nguyên liệu (duoc-CR-798) dùng chung khóa với Bảng giá VTBB: người giữ khóa đó vào màn ĐẦU (VTBB).
      if (path === appRoutes.procurement.packagingMaterialPrices) continue
      const can = grants(`${entity}.read`)
      expect(canOpenModule(procurementModule as ErpModule, can), entity).toBe(true)
      const landing = firstAccessibleNavPath(procurementModule as ErpModule, can)
      expect(landing, entity).toBe(path)
      expect(canAccessRoute(procurementModule as ErpModule, landing ?? '', can), entity).toBe(true)
    }
  })

  it('never lands a price-list-only reader on the hidden Báo giá VTBB screen', () => {
    const can = grants('packaging_price_list.read')
    expect(packagingParent(can)?.children?.[0]?.path).toBe(appRoutes.procurement.packagingPrices)
  })

  it('blocks typing the URL directly without the key, including deeper paths', () => {
    for (const path of [...PACKAGING_PATHS, `${appRoutes.procurement.packagingPrices}/x`]) {
      expect(
        canAccessRoute(procurementModule as ErpModule, path, grants('purchase_order.read')),
      ).toBe(false)
    }
    expect(
      canAccessRoute(
        procurementModule as ErpModule,
        `${appRoutes.procurement.packagingPrices}/x`,
        grants('packaging_price_list.read'),
      ),
    ).toBe(true)
  })

  it('marks the root child end:true so it does not light up on the sub-screens', () => {
    const parent = procurementModule.nav.find((item) => item.label === PACKAGING_PARENT_LABEL)
    const root = parent?.children?.find((child) => child.path === appRoutes.procurement.packagingImpact)
    expect(root?.end).toBe(true)
  })

  it('sits inside the Mua hàng group right after Tra cứu thị trường', () => {
    const nav = procurementModule.nav
    const parentIndex = nav.findIndex((item) => item.label === PACKAGING_PARENT_LABEL)
    expect(nav[parentIndex]?.group).toBe('Mua hàng')
    expect(nav[parentIndex - 1]?.label).toBe('Tra cứu thị trường')
  })

  it('registers a route for every menu path', () => {
    const routePaths = procurementModule.routes.map((route) => route.path)
    for (const path of PACKAGING_PATHS) expect(routePaths).toContain(path)
  })
})
