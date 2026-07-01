import { createContext, useContext, useState, ReactNode } from 'react'
import { api } from '../api/client'

type Perms = Record<string, Record<string, boolean | string>>
type User = { id: number; full_name: string; email: string; phone?: string; department_name?: string; avatar?: string; permissions: Perms }
type Ctx = {
  user: User | null
  login: (username: string, password: string) => Promise<void>
  loginGoogle: (credential: string) => Promise<void>
  logout: () => void
  can: (entity: string, action: string) => boolean
  updateUser: (u: Partial<User>) => void
}

const AuthCtx = createContext<Ctx>({} as Ctx)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const s = localStorage.getItem('user')
    return s ? JSON.parse(s) : null
  })

  async function login(username: string, password: string) {
    const r = await api.post('/api/auth/login', { username, password })
    const { access_token, refresh_token, user: loggedUser } = r.data.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    localStorage.setItem('user', JSON.stringify(loggedUser))
    setUser(loggedUser)
  }

  async function loginGoogle(credential: string) {
    const r = await api.post('/api/auth/google', { credential })
    const { access_token, refresh_token, user: loggedUser } = r.data.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    localStorage.setItem('user', JSON.stringify(loggedUser))
    setUser(loggedUser)
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

  function updateUser(u: Partial<User>) {
    if (!user) return
    const nextUser = { ...user, ...u }
    localStorage.setItem('user', JSON.stringify(nextUser))
    setUser(nextUser)
  }

  return <AuthCtx.Provider value={{ user, login, loginGoogle, logout, can, updateUser }}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)
