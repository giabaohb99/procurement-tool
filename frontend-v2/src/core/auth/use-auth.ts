import { useAuthStore } from './auth-store'

/** Hook tiện dụng cho component — khỏi phải nhớ hình dạng của store. */
export function useAuth() {
  const user = useAuthStore((s) => s.user)
  const isLoggingIn = useAuthStore((s) => s.isLoggingIn)
  const login = useAuthStore((s) => s.login)
  const logout = useAuthStore((s) => s.logout)
  const setUser = useAuthStore((s) => s.setUser)

  return { user, isAuthenticated: !!user, isLoggingIn, login, logout, setUser }
}
