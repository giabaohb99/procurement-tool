import type { ErpModule } from '@/app/router/module-definition'
// ⚠️ Chỉ được import từ component nằm trong trang lazy — KHÔNG từ `config/` hay `routes.tsx`:
// module-registry nạp routes của phân hệ Báo cáo, import ngược lại tạo vòng.
import { allModules } from '@/app/router/module-registry'

export interface RouteLabel {
  /** Tên phân hệ; rỗng khi không nhận ra route. */
  module: string
  screen: string
  /** Có nhận ra được route trong menu hiện tại hay không. */
  known: boolean
}

const stripQuery = (path: string) => path.split(/[?#]/, 1)[0]

/**
 * Route MẪU (`/procurement/purchase-orders/:id`) → {phân hệ, màn}: dò mục menu có
 * đường dẫn là tiền tố DÀI NHẤT của route. Phần còn lại bắt đầu bằng `:` thì là
 * trang chi tiết. Không khớp (màn của giao diện cũ, màn đã gỡ) → "Giao diện cũ".
 */
export function labelRoute(pattern: string, modules: readonly ErpModule[]): RouteLabel {
  let best: { module: ErpModule; label: string; path: string } | null = null
  for (const module of modules) {
    const items = [
      { label: 'Tổng quan', path: module.path },
      ...module.nav.flatMap((i) => [i, ...(i.children ?? [])]),
    ]
    for (const item of items) {
      const path = stripQuery(item.path)
      if (!path || path === '/') continue
      if (pattern !== path && !pattern.startsWith(`${path}/`)) continue
      if (!best || path.length > best.path.length) best = { module, label: item.label, path }
    }
  }
  if (!best) return { module: '', screen: `Giao diện cũ: ${pattern}`, known: false }
  const rest = pattern.slice(best.path.length).replace(/^\//, '')
  const suffix = !rest ? '' : rest.startsWith(':') ? ' (chi tiết)' : ` / ${rest}`
  return { module: best.module.title, screen: `${best.label}${suffix}`, known: true }
}

export function labelRouteInApp(pattern: string): RouteLabel {
  return labelRoute(pattern, allModules)
}
