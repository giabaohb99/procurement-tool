import axios from 'axios'

const baseURL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Tự động refresh access token khi gặp 401 (1 lần), thất bại thì về login
let refreshing: Promise<string> | null = null
api.interceptors.response.use(
  (r) => r,
  async (err) => {
    const orig: any = err.config
    if (err.response?.status === 401 && !orig?._retry && !orig?.url?.includes('/auth/')) {
      const rt = localStorage.getItem('refresh_token')
      if (!rt) { logout(); return Promise.reject(err) }
      orig._retry = true
      try {
        if (!refreshing) {
          refreshing = axios.post(`${baseURL}/api/auth/refresh`, { refresh_token: rt })
            .then((res) => res.data.data.access_token)
            .finally(() => { refreshing = null })
        }
        const newToken = await refreshing
        localStorage.setItem('token', newToken)
        orig.headers.Authorization = `Bearer ${newToken}`
        return api(orig)
      } catch {
        logout()
      }
    }
    return Promise.reject(err)
  },
)

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
  if (location.pathname !== '/login') location.href = '/login'
}
