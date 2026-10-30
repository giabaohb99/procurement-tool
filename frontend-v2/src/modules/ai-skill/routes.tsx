import { BookOpen, KeyRound, LayoutDashboard, Plug, ScrollText, Settings2 } from 'lucide-react'
import { Navigate } from 'react-router-dom'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

const SETS_PATH = `${appRoutes.aiSkill.root}/sets`
const SKILLS_PATH = `${appRoutes.aiSkill.root}/skills`

/**
 * Phân hệ KHO SKILL AI (doc/erp/21, K5 bao-CR-623) — cẩm nang công ty viết cho AI đọc, cộng phần quản trị khóa kết
 * nối AI riêng của nhân sự và nhật ký lượt gọi.
 *
 * Thẻ phân hệ hiện khi người dùng đọc được `ai_skill` HOẶC `ai_mcp_key_admin` (Agent 1 chốt) — không khai `entity` ở
 * cấp phân hệ vì nó chỉ nhận một khóa; `canOpenModule` đếm mục menu còn hiện, nên mỗi mục tự gác khóa của mình là đủ.
 * Màn "AI của tôi" của từng người nằm ở Trang cá nhân (`/me?tab=ai-connect`), ai cũng có — không ở đây.
 */
export const aiSkillModule: ErpModule = {
  id: 'ai-skill',
  title: 'Kho skill AI',
  description: 'Cẩm nang công ty cho AI riêng của nhân sự, khóa kết nối và nhật ký sử dụng.',
  icon: BookOpen,
  path: appRoutes.aiSkill.root,
  accent: 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
  enabled: true,

  nav: [
    {
      //  Số liệu cần quyền quản lý bot AI (`agent_group.read`); gác mục theo hai khóa của phân hệ để thẻ phân hệ không
      //  mở cho người chỉ quản lý bot — người thiếu `agent_group` mở ra thấy trang tự nói rõ, không ăn 403.
      label: 'Tổng quan',
      path: appRoutes.aiSkill.overview,
      icon: LayoutDashboard,
      entities: ['ai_skill', 'ai_mcp_key_admin'],
    },
    {
      //  `end` + `matchPaths`: không có `end` thì `/ai-skill` sáng ở MỌI trang con (Tổng quan, Khóa nhân sự…); còn chi
      //  tiết bộ và trang soạn vẫn phải làm sáng mục này.
      label: 'Bộ skill',
      path: appRoutes.aiSkill.root,
      icon: BookOpen,
      entity: 'ai_skill',
      end: true,
      matchPaths: [SETS_PATH, SKILLS_PATH],
    },
    //  Hai mục ẨN giữ chốt gác quyền cho `/ai-skill/sets/:id` và `/ai-skill/skills/:id` (gõ thẳng URL thiếu quyền thì bị
    //  chặn tử tế) — xem `ModuleNavItem.hidden`.
    { label: 'Chi tiết bộ skill', path: SETS_PATH, entity: 'ai_skill', hidden: true },
    { label: 'Soạn skill', path: SKILLS_PATH, entity: 'ai_skill', hidden: true },
    {
      label: 'Khóa nhân sự',
      path: appRoutes.aiSkill.keys,
      icon: KeyRound,
      entity: 'ai_mcp_key_admin',
    },
    {
      //  bao-CR-635: ứng dụng tự đăng ký OAuth (ChatGPT, claude.ai…). Đường API gác `agent_group.read` như Cấu hình —
      //  mục gác theo hai khóa của phân hệ, trang tự giải thích khi thiếu quyền quản lý bot AI.
      label: 'Ứng dụng AI đã kết nối',
      path: appRoutes.aiSkill.oauthClients,
      icon: Plug,
      entities: ['ai_skill', 'ai_mcp_key_admin'],
    },
    {
      //  Máy chủ tự giới hạn người thường chỉ xem lượt của mình — ai vào được phân hệ đều mở được.
      label: 'Nhật ký sử dụng',
      path: appRoutes.aiSkill.logs,
      icon: ScrollText,
      entities: ['ai_skill', 'ai_mcp_key_admin'],
    },
    //  Mục "Giới thiệu" (`/ai-skill/intro`) TẠM ẨN ngày 26/10/2026 để làm lại; trang `pages/ai-skill-intro-page.tsx` giữ
    //  nguyên. Bật lại: thêm lại mục `{ label: 'Giới thiệu', path: appRoutes.aiSkill.intro, icon: PlayCircle, entities:
    //  ['ai_skill', 'ai_mcp_key_admin'] }` ở đây và trả route bên dưới về `lazy` nạp `AiSkillIntroPage`.
    {
      //  Cấu hình cổng MCP (G7) đòi `agent_group.read` / `.write` như Tổng quan — gác mục theo hai khóa của phân hệ, trang
      //  tự giải thích khi thiếu quyền quản lý bot AI, tự chuyển chỉ xem khi thiếu quyền ghi.
      label: 'Cấu hình',
      path: appRoutes.aiSkill.settings,
      icon: Settings2,
      entities: ['ai_skill', 'ai_mcp_key_admin'],
    },
  ],

  routes: [
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
    //  Giới thiệu tạm ẩn (xem chú thích ở `nav`): link cũ / dấu trang chuyển về Tổng quan thay vì trang trắng.
    { path: appRoutes.aiSkill.intro, element: <Navigate to={appRoutes.aiSkill.overview} replace /> },
    {
      path: appRoutes.aiSkill.settings,
      lazy: async () => ({
        Component: (await import('./pages/ai-skill-settings-page')).AiSkillSettingsPage,
      }),
    },
  ],
}
