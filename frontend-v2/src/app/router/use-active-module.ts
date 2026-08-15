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

  return (
    [...moduleRegistry]
      .sort((a, b) => b.path.length - a.path.length)
      .find((m) => pathname === m.path || pathname.startsWith(`${m.path}/`)) ?? null
  )
}
