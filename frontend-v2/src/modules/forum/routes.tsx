import { Library, Megaphone, MessagesSquare, UserRound } from 'lucide-react'
import { Navigate } from 'react-router-dom'

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
  accent: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  enabled: true,
  customLayout: true,

  nav: [
    // «Diễn đàn» đứng trước và là màn mặc định của phân hệ (sếp chốt 03/09/2026).
    {
      label: 'Diễn đàn',
      path: appRoutes.forum.boards,
      icon: Library,
    },
    {
      label: 'Bảng tin',
      path: appRoutes.forum.feed,
      icon: MessagesSquare,
      end: true,
    },
    {
      label: 'Thông báo',
      path: appRoutes.forum.announcements,
      icon: Megaphone,
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
              // `/forum` = Diễn đàn (danh sách box). Bảng tin dời sang `/forum/feed`;
              // link cũ trỏ `/forum` vẫn sống nhờ chuyển hướng này.
              index: true,
              element: <Navigate to={appRoutes.forum.boards} replace />,
            },
            {
              path: 'feed',
              lazy: async () => ({
                Component: (await import('./pages/forum-feed-page')).ForumFeedPage,
              }),
            },
            {
              path: 'boards',
              lazy: async () => ({
                Component: (await import('./pages/forum-boards-page')).ForumBoardsPage,
              }),
            },
            {
              path: 'boards/:id',
              lazy: async () => ({
                Component: (await import('./pages/forum-board-threads-page'))
                  .ForumBoardThreadsPage,
              }),
            },
            {
              path: 'announcements',
              lazy: async () => ({
                Component: (await import('./pages/forum-announcements-page'))
                  .ForumAnnouncementsPage,
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
            {
              // Tìm bài (CR-263) — mở cho MỌI người, kết quả backend tự lọc audience.
              path: 'search',
              lazy: async () => ({
                Component: (await import('./pages/forum-search-page')).ForumSearchPage,
              }),
            },
            {
              // Tab «Quản trị» (CR-263) — trang tự đá về Diễn đàn khi thiếu grant.
              path: 'admin',
              lazy: async () => ({
                Component: (await import('./pages/forum-admin-page')).ForumAdminPage,
              }),
            },
          ],
        },
      ],
    },
  ],
}
