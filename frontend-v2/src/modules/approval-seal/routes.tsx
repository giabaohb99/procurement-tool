import { LayoutDashboard, Stamp } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ DUYỆT DẤU — chưa làm xong, hiện ở dạng "Sắp có".
 *
 * Backend mới có `model.py` + `schema.py`, chưa có endpoint; trang dưới đây mới
 * là chỗ để tên. Bật lên khi có màn thật, không thì người dùng bấm vào ô rỗng.
 */
export const approvalSealModule: ErpModule = {
  id: 'approval-seal',
  title: 'Duyệt dấu',
  description: 'Trình ký, duyệt và đóng dấu chứng từ, hợp đồng, văn bản hành chính.',
  icon: Stamp,
  path: appRoutes.approvalSeal.root,
  accent: 'bg-red-500/10 text-red-600 dark:text-red-400',
  enabled: false,

  nav: [
    { label: 'Tổng quan', path: appRoutes.approvalSeal.root, icon: LayoutDashboard, end: true },
  ],

  routes: [
    {
      path: appRoutes.approvalSeal.root,
      lazy: async () => ({
        Component: (await import('./pages/approval-seal-page')).ApprovalSealPage,
      }),
    },
  ],
}
