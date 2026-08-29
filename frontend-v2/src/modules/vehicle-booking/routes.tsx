import { ClipboardList } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'
import { CarTileIcon } from './components/booking-type-icons'

/**
 * Phân hệ ĐẶT XE NỘI BỘ (DEGO Booking Auto).
 *
 * Lát dọc MVP: tạo & theo dõi yêu cầu của người dùng (2 loại — công tác / giao
 * hàng). Điều phối, tài xế, danh mục Xe/Tài xế và luồng duyệt sẽ mở ở đợt sau.
 */
export const vehicleBookingModule: ErpModule = {
  id: 'vehicle-booking',
  title: 'Đặt xe',
  description: 'Đặt xe công tác và giao hàng nội bộ, theo dõi trạng thái phiếu.',
  icon: CarTileIcon,
  path: appRoutes.vehicleBooking.root,
  accent: 'bg-orange-500/10 text-orange-600 dark:text-orange-400',
  enabled: true,

  // Tạo/sửa mở dạng POPUP ngay trên danh sách (case UI C-01) nên KHÔNG có route
  // /new riêng — nút "Tạo yêu cầu" nằm trong màn danh sách.
  nav: [
    {
      label: 'Yêu cầu đặt xe',
      path: appRoutes.vehicleBooking.root,
      icon: ClipboardList,
      entity: 'vehicle_booking',
      end: true,
    },
  ],

  routes: [
    {
      path: appRoutes.vehicleBooking.root,
      lazy: async () => ({
        Component: (await import('./pages/vehicle-booking-list-page')).VehicleBookingListPage,
      }),
    },
    {
      path: appRoutes.vehicleBooking.detail(':id'),
      lazy: async () => ({
        Component: (await import('./pages/vehicle-booking-detail-page')).VehicleBookingDetailPage,
      }),
    },
  ],
}
