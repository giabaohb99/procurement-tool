import { createContext, useContext, useState, ReactNode } from 'react'
import { api } from '../api/client'

type Perms = Record<string, Record<string, boolean | string>>
type User = { id: number; full_name: string; email: string; permissions: Perms }
type Ctx = {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  can: (entity: string, action: string) => boolean
}

const AuthCtx = createContext<Ctx>({} as Ctx)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const s = localStorage.getItem('user')
    return s ? JSON.parse(s) : null
  })

  async function login(username: string, password: string) {
    const r = await api.post('/api/auth/login', { username, password })
    const { access_token, refresh_token, user } = r.data.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    localStorage.setItem('user', JSON.stringify(user))
    setUser(user)
  }

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    setUser(null)
  }

  function can(entity: string, action: string) {
    return !!user?.permissions?.[entity]?.[action]
  }

  return <AuthCtx.Provider value={{ user, login, logout, can }}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
