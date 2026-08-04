import { JSX } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { useAuth } from '@/auth/auth-context'
import AdminLayout from '@/layouts/admin-layout'
import PortalLayout from '@/layouts/portal-layout'
import AdminArticle from '@/pages/admin-article'
import AdminFaq from '@/pages/admin-faq'
import AdminHistory from '@/pages/admin-history'
import AdminHome from '@/pages/admin-home'
import Login from '@/pages/login'
import PortalHome from '@/pages/portal-home'
import PortalFaq from '@/pages/portal-faq'
import PortalNode from '@/pages/portal-node'

/** Chặn truy cập khi chưa đăng nhập — API help-center yêu cầu token. */
function Protected({ children }: { children: JSX.Element }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      {/* Khu QUẢN TRỊ — AdminLayout tự chặn user không có quyền help_article/write */}
      <Route path="/admin" element={<Protected><AdminLayout /></Protected>}>
        <Route index element={<AdminHome />} />
        <Route path="lich-su" element={<AdminHistory />} />
        <Route path="faq" element={<AdminFaq />} />
        <Route path=":id" element={<AdminArticle />} />
      </Route>

      {/* Khu NGƯỜI DÙNG — chỉ đọc. /:id tự phân nhánh danh mục / bài viết (xem portal-node) */}
      <Route path="/" element={<Protected><PortalLayout /></Protected>}>
        <Route index element={<PortalHome />} />
        <Route path="cau-hoi-thuong-gap" element={<PortalFaq />} />
        <Route path=":id" element={<PortalNode />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
