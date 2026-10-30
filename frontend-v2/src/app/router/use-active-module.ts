import { useLocation } from 'react-router-dom'

import { moduleRegistry } from './module-registry'
import type { ErpModule } from './module-definition'

/**
 * Module ứng với URL hiện tại, `null` khi đang ở màn chọn phân hệ.
 * Khớp theo tiền tố đường dẫn, ưu tiên path DÀI nhất để module có path lồng
 * nhau (vd `/sales` và `/sales-return`) không bắt nhầm nhau.
 */
export function useActiveModule(): ErpModule | null {
  const { pathname } = useLocation()
  return findModuleByPath(pathname)
}

/**
 * Tách khỏi hook để bài kiểm gọi thẳng được. Xét cả đường gốc phụ (`extraPaths`) — phân hệ AI gộp từ hai phân hệ cũ
 * nên `/ai-skill/...` và `/assistant/...` đều phải ra cùng một phân hệ (bao-CR-696).
 */
export function findModuleByPath(pathname: string, modules: ErpModule[] = moduleRegistry): ErpModule | null {
  const candidates = modules.flatMap((m) => [m.path, ...(m.extraPaths ?? [])].map((root) => ({ m, root })))
  const hit = candidates
    .sort((a, b) => b.root.length - a.root.length)
    .find(({ root }) => pathname === root || pathname.startsWith(`${root}/`))
  return hit?.m ?? null
}
