import { Sparkles } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ TRỢ LÝ AI (AI-1) — hỏi đáp trên nền gói tri thức nội bộ.
 *
 * Chỉ ban lãnh đạo thấy: gác bằng entity `assistant` (backend seed `assistant.read`
 * cho admin / pur_manager / company_head). Bật/tắt sâu hơn ở máy chủ bằng cờ
 * `AI_ENABLED`; khi tắt, endpoint trả 403 và trang tự hiện thông báo chưa sẵn sàng.
 */
export const assistantModule: ErpModule = {
  id: 'assistant',
  title: 'Trợ lý AI',
  description: 'Hỏi đáp trên nền gói tri thức nội bộ.',
  icon: Sparkles,
  path: appRoutes.assistant.root,
  accent: 'bg-violet-50 text-violet-600',
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
  ],

  routes: [
    {
      path: appRoutes.assistant.root,
      lazy: async () => ({
        Component: (await import('./pages/assistant-page')).AssistantPage,
      }),
    },
  ],
}
