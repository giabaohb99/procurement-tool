import { Car, LayoutDashboard } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

export const vehicleBookingModule: ErpModule = {
  id: 'vehicle-booking',
  title: 'Đặt xe',
  description: 'Duyệt yêu cầu sử dụng xe nội bộ, điều phối xe và tài xế.',
  icon: Car,
  path: appRoutes.vehicleBooking.root,
  accent: 'bg-orange-50 text-orange-600',
  enabled: true,

  nav: [
    { label: 'Tổng quan', path: appRoutes.vehicleBooking.root, icon: LayoutDashboard, end: true },
  ],

  routes: [
    {
      path: appRoutes.vehicleBooking.root,
      lazy: async () => ({
        Component: (await import('./pages/vehicle-booking-page')).VehicleBookingPage,
      }),
    },
  ],
}
