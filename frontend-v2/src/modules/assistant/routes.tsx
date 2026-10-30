import type { RouteObject } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Route của TRỢ LÝ AI (AI-1) — hỏi đáp trên nền gói tri thức nội bộ, cộng nhóm chat và người dùng bot Telegram.
 *
 * bao-CR-696 (30/10/2026): không còn là phân hệ riêng — gộp vào phân hệ **AI** (`modules/ai/routes.tsx`), nơi khai
 * menu và quyền từng mục. Ở đây chỉ còn bảng route, đường `/assistant/...` giữ nguyên. Bật/tắt sâu hơn ở máy chủ
 * bằng cờ `AI_ENABLED`; khi tắt, endpoint trả 403 và trang tự hiện thông báo chưa sẵn sàng.
 */
export const assistantRoutes: RouteObject[] = [
  {
    path: appRoutes.assistant.root,
    lazy: async () => ({
      Component: (await import('./pages/assistant-page')).AssistantPage,
    }),
  },
  {
    path: appRoutes.assistant.groups,
    lazy: async () => ({
      Component: (await import('./pages/chat-group-list-page')).ChatGroupListPage,
    }),
  },
  {
    path: appRoutes.assistant.botUsers,
    lazy: async () => ({
      Component: (await import('./pages/bot-user-list-page')).BotUserListPage,
    }),
  },
  {
    path: appRoutes.assistant.group(':id'),
    lazy: async () => ({
      Component: (await import('./pages/chat-group-detail-page')).ChatGroupDetailPage,
    }),
  },
]
