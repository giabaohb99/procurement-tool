import { Car, LayoutDashboard } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Phân hệ ĐẶT XE — chưa làm xong, hiện ở dạng "Sắp có".
 *
 * Backend mới có `model.py` + `schema.py`, chưa có endpoint; trang dưới đây mới
 * là chỗ để tên. Bật lên khi có màn thật, không thì người dùng bấm vào ô rỗng.
 */
export const vehicleBookingModule: ErpModule = {
  id: 'vehicle-booking',
  title: 'Đặt xe',
  description: 'Duyệt yêu cầu sử dụng xe nội bộ, điều phối xe và tài xế.',
  icon: Car,
  path: appRoutes.vehicleBooking.root,
  accent: 'bg-orange-500/10 text-orange-600 dark:text-orange-400',
  enabled: false,

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
