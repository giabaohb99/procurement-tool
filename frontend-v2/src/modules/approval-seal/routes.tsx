import { LayoutDashboard, Stamp } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

export const approvalSealModule: ErpModule = {
  id: 'approval-seal',
  title: 'Duyệt dấu',
  description: 'Trình ký, duyệt và đóng dấu chứng từ, hợp đồng, văn bản hành chính.',
  icon: Stamp,
  path: appRoutes.approvalSeal.root,
  accent: 'bg-red-50 text-red-600',
  enabled: true,

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
