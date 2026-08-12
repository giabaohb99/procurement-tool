import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
import { useAuthSync } from '@/core/auth/use-auth-sync'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Route layout chặn khách chưa đăng nhập.
 * Cũng là nơi gắn `useAuthSync` — cần nằm trong router để điều hướng được,
 * và mọi màn hình cần đăng nhập đều đi qua đây.
 *
 * ⚠️ Chỉ là trải nghiệm người dùng. Dữ liệu được bảo vệ ở backend.
 */
export function ProtectedRoute() {
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  useAuthSync()

  if (!isAuthenticated) {
    // Nhớ trang đang định vào để đăng nhập xong quay lại đúng chỗ.
    return <Navigate to={appRoutes.login} replace state={{ from: location }} />
  }

  return <Outlet />
}
