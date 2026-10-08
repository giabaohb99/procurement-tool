import { MessagesSquare, Sparkles } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ TRỢ LÝ AI (AI-1) — hỏi đáp trên nền gói tri thức nội bộ.
 *
 * Chỉ ban lãnh đạo thấy: gác bằng entity `assistant` (backend seed `assistant.read`
 * cho admin / pur_manager / company_head). Bật/tắt sâu hơn ở máy chủ bằng cờ
 * `AI_ENABLED`; khi tắt, endpoint trả 403 và trang tự hiện thông báo chưa sẵn sàng.
 *
 * ai-CR-123: mục «Nhóm chat» — tin, tệp, bản tóm tắt bot đã ghi ở nhóm Telegram / Zalo. Không gác thêm khóa: ai vào
 * được phân hệ đều xem được nhóm MÌNH là thành viên; khóa `agent_group` mở thêm «Tất cả nhóm» trong trang.
 */
export const assistantModule: ErpModule = {
  id: 'assistant',
  title: 'Trợ lý AI',
  description: 'Hỏi đáp trên nền gói tri thức nội bộ.',
  icon: Sparkles,
  path: appRoutes.assistant.root,
  accent: 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
  enabled: true,
  entity: 'assistant',

  nav: [
    {
      label: 'Trợ lý AI',
      path: appRoutes.assistant.root,
      icon: Sparkles,
      end: true,
      entity: 'assistant',
    },
    {
      label: 'Nhóm chat',
      path: appRoutes.assistant.groups,
      icon: MessagesSquare,
      entity: 'assistant',
    },
  ],

  routes: [
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
      path: appRoutes.assistant.group(':id'),
      lazy: async () => ({
        Component: (await import('./pages/chat-group-detail-page')).ChatGroupDetailPage,
      }),
    },
  ],
}
