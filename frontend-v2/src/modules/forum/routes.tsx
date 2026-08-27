import { MessagesSquare, UserRound } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'
import { RouteErrorPage } from '@/shared/ui/route-error-page'

/**
 * Phân hệ DIỄN ĐÀN nội bộ (QĐ-D6) — bảng tin kiểu mạng xã hội cho toàn công ty.
 *
 * `customLayout: true`: không dùng khung sidebar `ModuleLayout` — cả nhánh
 * `/forum` chạy trong `ForumLayout` một cột khai ngay dưới đây. Không khai
 * `entity`: ai đăng nhập cũng vào được, quyền xem TỪNG BÀI do backend lọc theo
 * `audience` (doc `erp/dien-dan/01` mục 4.2), không theo grant RBAC.
 */
export const forumModule: ErpModule = {
  id: 'forum',
  title: 'Diễn đàn',
  description: 'Bảng tin nội bộ: bài viết, hình ảnh và trao đổi toàn công ty.',
  icon: MessagesSquare,
  path: appRoutes.forum.root,
  accent: 'bg-blue-50 text-blue-600',
  enabled: true,
  customLayout: true,

  nav: [
    {
      label: 'Bảng tin',
      path: appRoutes.forum.root,
      icon: MessagesSquare,
      end: true,
    },
    {
      label: 'Trang của tôi',
      path: appRoutes.forum.me,
      icon: UserRound,
      end: true,
    },
  ],

  routes: [
    {
      path: appRoutes.forum.root,
      lazy: async () => ({
        Component: (await import('./components/forum-layout')).ForumLayout,
      }),
      // Lỗi ở chính layout thay cả màn; lỗi của trang con rơi vào boundary
      // trong `children` để người dùng còn thanh trên mà đi tiếp — cùng khuôn
      // hai tầng của `app-router.tsx`.
      errorElement: <RouteErrorPage />,
      children: [
        {
          errorElement: <RouteErrorPage />,
          children: [
            {
              index: true,
              lazy: async () => ({
                Component: (await import('./pages/forum-feed-page')).ForumFeedPage,
              }),
            },
            {
              path: 'posts/:id',
              lazy: async () => ({
                Component: (await import('./pages/forum-post-page')).ForumPostPage,
              }),
            },
            {
              path: 'me',
              lazy: async () => ({
                Component: (await import('./pages/forum-profile-page')).ForumProfilePage,
              }),
            },
            {
              path: 'users/:id',
              lazy: async () => ({
                Component: (await import('./pages/forum-profile-page')).ForumProfilePage,
              }),
            },
          ],
        },
      ],
    },
  ],
}
