import { Coffee, LayoutDashboard } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

export const degoCoffeeModule: ErpModule = {
  id: 'dego-coffee',
  title: 'Dego Coffee',
  description: 'Quản lý và tra cứu điểm thưởng, đặt nước trực tuyến tại quán cà phê nội bộ.',
  icon: Coffee,
  path: appRoutes.degoCoffee.root,
  accent: 'bg-amber-50 text-amber-600',
  enabled: false,

  nav: [
    { label: 'Tổng quan', path: appRoutes.degoCoffee.root, icon: LayoutDashboard, end: true },
  ],

  routes: [
    {
      path: appRoutes.degoCoffee.root,
      lazy: async () => ({
        Component: (await import('./pages/dego-coffee-page')).DegoCoffeePage,
      }),
    },
  ],
}
