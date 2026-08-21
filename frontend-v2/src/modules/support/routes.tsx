import { LifeBuoy } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ HỖ TRỢ — phiếu hỗ trợ (ticket).
 *
 * Backend giới hạn theo phạm vi: người gửi chỉ thấy phiếu của mình, người có
 * vai trò `support` (proxy FE là quyền `ticket.delete`) thấy tất cả và nhận /
 * trả / đổi trạng thái phiếu. Chi tiết đặt ở `/support/tickets/:id` để link
 * thông báo kiểu cũ `/tickets/{id}` dịch được sang (xem `notification-link.ts`).
 */
export const supportModule: ErpModule = {
  id: 'support',
  title: 'Hỗ trợ',
  description: 'Phiếu hỗ trợ người dùng và trao đổi xử lý.',
  icon: LifeBuoy,
  path: appRoutes.support.root,
  accent: 'bg-teal-50 text-teal-600',
  enabled: true,
  entity: 'ticket',

  nav: [
    {
      label: 'Phiếu hỗ trợ',
      path: appRoutes.support.root,
      icon: LifeBuoy,
      end: true,
      entity: 'ticket',
    },
  ],

  routes: [
    {
      path: appRoutes.support.root,
      lazy: async () => ({
        Component: (await import('./pages/ticket-list-page')).TicketListPage,
      }),
    },
    {
      path: '/support/tickets/:id',
      lazy: async () => ({
        Component: (await import('./pages/ticket-detail-page')).TicketDetailPage,
      }),
    },
  ],
}
