import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { t } from '@/core/i18n/use-translation'
import { appRoutes } from '@/shared/constants/app-routes'
import { authEvents } from './auth-events'
import { useAuthStore } from './auth-store'

/**
 * Nối sự kiện của http-client vào state + điều hướng.
 * PHẢI gọi bên trong router (cần `useNavigate`) — hiện đặt ở `ProtectedRoute`.
 */
export function useAuthSync() {
  const navigate = useNavigate()

  useEffect(() => {
    // Refresh token trả kèm hồ sơ mới -> cập nhật tên, phòng ban, phân quyền
    // mà không bắt người dùng đăng xuất đăng nhập lại.
    const offRefreshed = authEvents.onUserRefreshed((user) => {
      useAuthStore.getState().setUser(user)
    })

    const offExpired = authEvents.onSessionExpired(() => {
      useAuthStore.getState().logout()
      toast.error(t('auth.sessionExpired'))
      navigate(appRoutes.login, { replace: true })
    })

    return () => {
      offRefreshed()
      offExpired()
    }
  }, [navigate])
}
