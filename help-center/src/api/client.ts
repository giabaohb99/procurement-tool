import axios from 'axios'
import { toast } from 'sonner'

// Rỗng = gọi tương đối (cùng origin) -> đi qua proxy Vite (/api -> api:8000).
// Nhờ vậy dùng được từ localhost, LAN (192.168.x.x), Cloudflare... không dính CORS.
// Production set VITE_API_URL lúc build (domain thật) nên vẫn dùng URL tuyệt đối.
const baseURL = (import.meta as any).env?.VITE_API_URL || ''

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
      return Promise.reject(err)
    }
    // Popup lỗi cho HÀNH ĐỘNG của người dùng (POST/PATCH/PUT/DELETE). GET (nạp nền) để màn tự xử lý.
    // Caller có thể đặt config._silent = true để tự hiển thị lỗi.
    const method = (orig?.method || 'get').toLowerCase()
    if (method !== 'get' && !orig?._silent) {
      const msg = err.response?.data?.error?.message || err.response?.data?.message || err.message || 'Có lỗi xảy ra, vui lòng thử lại'
      toast.error(msg)
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
