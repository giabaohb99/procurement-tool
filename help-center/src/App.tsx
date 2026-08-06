import { JSX } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { useAuth } from '@/auth/auth-context'
import AdminLayout from '@/layouts/admin-layout'
import PortalLayout from '@/layouts/portal-layout'
import AdminArticle from '@/pages/admin-article'
import AdminFaq from '@/pages/admin-faq'
import AdminFaqEditor from '@/pages/admin-faq-editor'
import AdminHistory from '@/pages/admin-history'
import AdminHomeLayout from '@/pages/admin-home-layout'
import AdminHome from '@/pages/admin-home'
import Login from '@/pages/login'
import PortalHome from '@/pages/portal-home'
import PortalFaq from '@/pages/portal-faq'
import PortalNode from '@/pages/portal-node'

/** Chặn khu QUẢN TRỊ khi chưa đăng nhập. Khu người dùng để công khai. */
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
        <Route path="trang-chu" element={<AdminHomeLayout />} />
        <Route path="lich-su" element={<AdminHistory />} />
        <Route path="faq" element={<AdminFaq />} />
        <Route path="faq/moi" element={<AdminFaqEditor />} />
        <Route path="faq/:faqId" element={<AdminFaqEditor />} />
        <Route path=":id" element={<AdminArticle />} />
      </Route>

      {/* Khu NGƯỜI DÙNG — CÔNG KHAI, chỉ đọc. /:slug tự phân nhánh danh mục / bài viết (xem portal-node) */}
      <Route path="/" element={<PortalLayout />}>
        <Route index element={<PortalHome />} />
        <Route path="cau-hoi-thuong-gap" element={<PortalFaq />} />
        <Route path=":slug" element={<PortalNode />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
