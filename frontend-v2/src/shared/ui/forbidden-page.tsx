import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'

/**
 * 403 — hiện bên trong khung phân hệ (còn menu trái) để người dùng chọn màn khác
 * mình có quyền, thay vì mất trắng. Chỉ là trải nghiệm: backend mới là chốt chặn.
 */
export function ForbiddenPage() {
  return (
    <ErrorState
      code="403"
      title="Không có quyền truy cập"
      description="Tài khoản của bạn chưa được cấp quyền xem màn hình này. Hãy liên hệ quản trị nếu cần."
    >
      <Button asChild>
        <Link to={appRoutes.launcher}>Về màn chọn phân hệ</Link>
      </Button>
    </ErrorState>
  )
}
