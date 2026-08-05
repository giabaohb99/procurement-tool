import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

import { api } from '@/api/client'

// Auth cho app Help Center — dùng CHUNG tài khoản & API với hệ thống Thu mua.
//
// Khu người dùng (/) là CÔNG KHAI: không đăng nhập vẫn đọc được tài liệu.
// Đăng nhập chỉ cần cho khu quản trị (/admin).
//
// Bàn giao phiên từ app Thu mua (cổng khác → không chung localStorage):
// link sang đây kèm token ở HASH `#t=<access>&r=<refresh>`; ta nạp vào localStorage
// rồi xóa hash ngay. Dùng hash vì phần này KHÔNG được gửi lên server.

type Perms = Record<string, Record<string, boolean | string>>

type User = {
  id: number
  full_name: string
  email: string
  emp_code?: string
  avatar?: string
  position?: string
  permissions: Perms
}

type Ctx = {
  user: User | null
  login: (username: string, password: string) => Promise<User>
  logout: () => void
  can: (entity: string, action: string) => boolean
}

const AuthCtx = createContext<Ctx>({} as Ctx)

/** Lấy token bàn giao ở hash (nếu có), lưu lại và xóa khỏi URL. Trả về true nếu có token mới. */
function consumeHandoff(): boolean {
  const hash = window.location.hash.replace(/^#/, '')
  if (!hash.includes('t=')) return false
  const p = new URLSearchParams(hash)
  const t = p.get('t')
  if (!t) return false
  localStorage.setItem('token', t)
  const r = p.get('r')
  if (r) localStorage.setItem('refresh_token', r)
  // Xóa token khỏi thanh địa chỉ + lịch sử ngay lập tức
  window.history.replaceState(null, '', window.location.pathname + window.location.search)
  return true
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [handoff] = useState(consumeHandoff)
  const [user, setUser] = useState<User | null>(() => {
    if (handoff) return null   // có token mới → lấy lại hồ sơ từ /me bên dưới
    const s = localStorage.getItem('user')
    return s ? JSON.parse(s) : null
  })

  // Có token (bàn giao từ app Thu mua, hoặc phiên cũ chưa có hồ sơ) → nạp hồ sơ + quyền
  useEffect(() => {
    if (!localStorage.getItem('token')) return
    if (user && !handoff) return
    api.get('/api/auth/me', { _silent: true } as any)
      .then((r) => {
        const u = r.data.data
        localStorage.setItem('user', JSON.stringify(u))
        setUser(u)
      })
      .catch(() => {
        // Token hỏng/hết hạn: dọn sạch, vẫn xem được khu công khai
        localStorage.removeItem('token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        setUser(null)
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [handoff])

  async function login(username: string, password: string) {
    const r = await api.post('/api/auth/login', { username, password })
    const { access_token, refresh_token, user: loggedUser } = r.data.data
    localStorage.setItem('token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    localStorage.setItem('user', JSON.stringify(loggedUser))
    setUser(loggedUser)
    return loggedUser as User
  }

  function logout() {
    // Ghi log đăng xuất (best-effort) trước khi xóa token — không chặn nếu lỗi mạng.
    api.post('/api/auth/logout', null, { _silent: true } as any).catch(() => {})
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
