import { Navigate, type RouteObject } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Route của KHO SKILL AI (doc/erp/21, K5 bao-CR-623) — cẩm nang công ty viết cho AI đọc, kết nối AI riêng của nhân
 * sự, nhật ký lượt gọi và cấu hình cổng.
 *
 * bao-CR-696 (30/10/2026): không còn là phân hệ riêng — gộp vào phân hệ **AI** (`modules/ai/routes.tsx`), nơi khai
 * menu và quyền từng mục. Ở đây chỉ còn bảng route, đường `/ai-skill/...` giữ nguyên.
 */
export const aiSkillRoutes: RouteObject[] = [
  {
    path: appRoutes.aiSkill.overview,
    lazy: async () => ({
      Component: (await import('./pages/ai-overview-page')).AiOverviewPage,
    }),
  },
  {
    path: appRoutes.aiSkill.root,
    lazy: async () => ({
      Component: (await import('./pages/skill-set-list-page')).SkillSetListPage,
    }),
  },
  {
    path: appRoutes.aiSkill.setDetail(':id'),
    lazy: async () => ({
      Component: (await import('./pages/skill-set-detail-page')).SkillSetDetailPage,
    }),
  },
  {
    path: appRoutes.aiSkill.skillEditor(':id'),
    lazy: async () => ({
      Component: (await import('./pages/skill-editor-page')).SkillEditorPage,
    }),
  },
  {
    path: appRoutes.aiSkill.keys,
    lazy: async () => ({
      Component: (await import('./pages/key-admin-page')).KeyAdminPage,
    }),
  },
  {
    path: appRoutes.aiSkill.oauthClients,
    lazy: async () => ({
      Component: (await import('./pages/oauth-clients-page')).OAuthClientsPage,
    }),
  },
  {
    path: appRoutes.aiSkill.logs,
    lazy: async () => ({
      Component: (await import('./pages/call-log-page')).CallLogPage,
    }),
  },
  //  Giới thiệu TẠM ẨN từ 26/10/2026 để làm lại (trang `pages/ai-skill-intro-page.tsx` giữ nguyên): link cũ / dấu
  //  trang chuyển về Tổng quan thay vì trang trắng. Bật lại: thêm mục menu ở `modules/ai/routes.tsx` và trả route này
  //  về `lazy` nạp `AiSkillIntroPage`.
  { path: appRoutes.aiSkill.intro, element: <Navigate to={appRoutes.aiSkill.overview} replace /> },
  {
    path: appRoutes.aiSkill.settings,
    lazy: async () => ({
      Component: (await import('./pages/ai-skill-settings-page')).AiSkillSettingsPage,
    }),
  },
]
