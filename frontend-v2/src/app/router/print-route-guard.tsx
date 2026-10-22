import type { ComponentType } from 'react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { PRINT_ROUTE_ACCESS } from './print-route-access'

/** Trang chặn của bản in: nói rõ thiếu quyền gì, không dựng trang in nên không lộ dữ liệu. */
function PrintForbidden({ detail }: { detail: string }) {
  return (
    <ErrorState
      fullScreen
      code="403"
      title="Không có quyền mở bản in"
      description="Tài khoản của bạn chưa được cấp quyền xem bản in này. Hãy liên hệ quản trị nếu cần."
      detail={detail}
    >
      <Button asChild>
        <Link to={appRoutes.launcher}>Về màn chọn phân hệ</Link>
      </Button>
    </ErrorState>
  )
}

/**
 * Bọc một trang in bằng cổng quyền khai ở `PRINT_ROUTE_ACCESS`.
 * Route in chưa khai quyền thì ĐÓNG (fail-closed) — khác gác menu mặc định mở.
 * Chỉ là lớp giao diện: backend vẫn là chốt chặn.
 */
export function withPrintGuard(path: string, Page: ComponentType): ComponentType {
  function GuardedPrintPage() {
    const { can } = usePermission()
    const access = PRINT_ROUTE_ACCESS[path]
    if (!access) return <PrintForbidden detail="Route in chưa khai quyền" />
    if ('flow' in access || can(access.entity, access.action)) return <Page />
    return <PrintForbidden detail={`Cần quyền ${access.entity}:${access.action}`} />
  }
  return GuardedPrintPage
}

/**
 * Dùng cho `lazy` của route in: nạp trang rồi bọc cổng quyền quanh nó.
 * Gom ở đây để mỗi route in chỉ khai đường dẫn + trang, không thể quên cổng.
 */
export function guardedPrintLazy(path: string, loadPage: () => Promise<ComponentType>) {
  return async () => ({ Component: withPrintGuard(path, await loadPage()) })
}
