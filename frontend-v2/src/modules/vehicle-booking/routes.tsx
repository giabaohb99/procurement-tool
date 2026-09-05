import { ClipboardList, IdCard, Route } from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { appRoutes } from '@/shared/constants/app-routes'
import { CarTileIcon } from './components/booking-type-icons'

/**
 * Phân hệ ĐẶT XE NỘI BỘ (DEGO Booking Auto).
 *
 * Nghiệp vụ: tạo & theo dõi yêu cầu (2 loại — công tác / giao hàng). Danh mục:
 * quản lý Xe & Tài xế (khung CRUD chung). Điều phối, tài xế và luồng duyệt sẽ mở
 * ở đợt sau.
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
  // Tạo/sửa YÊU CẦU mở dạng POPUP ngay trên danh sách (case UI C-01). Danh mục
  // Xe/Tài xế dùng khung CRUD chung (bảng + chi tiết + popup).
  nav: [
    {
      label: 'Yêu cầu đặt xe',
      path: appRoutes.vehicleBooking.root,
      icon: ClipboardList,
      entity: 'vehicle_booking',
      end: true,
    },
    {
      label: 'Chuyến của tôi',
      path: appRoutes.vehicleBooking.myTrips,
      icon: Route,
      entity: 'vehicle_booking',
    },
    {
      label: 'Quản lý xe',
      // Icon sedan tự vẽ (viewBox 39×28) — dùng `currentColor` nên ĂN MÀU theo menu,
      // không ghim màu xanh; cùng dáng với thẻ phân hệ Đặt xe.
      path: appRoutes.vehicleBooking.vehicles,
      icon: CarTileIcon,
      entity: 'vehicle',
      group: 'Danh mục',
    },
    {
      label: 'Quản lý tài xế',
      path: appRoutes.vehicleBooking.drivers,
      icon: IdCard,
      entity: 'driver',
      group: 'Danh mục',
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
      path: appRoutes.vehicleBooking.myTrips,
      lazy: async () => ({
        Component: (await import('./pages/my-trips-page')).MyTripsPage,
      }),
    },
    {
      path: appRoutes.vehicleBooking.new,
      lazy: async () => ({
        Component: (await import('./pages/vehicle-booking-form-page')).VehicleBookingFormPage,
      }),
    },
    {
      path: appRoutes.vehicleBooking.edit(':id'),
      lazy: async () => ({
        Component: (await import('./pages/vehicle-booking-form-page')).VehicleBookingFormPage,
      }),
    },
    {
      path: appRoutes.vehicleBooking.vehicles,
      lazy: async () => ({
        Component: (await import('./pages/vehicle-list-page')).VehicleListPage,
      }),
    },
    {
      path: appRoutes.vehicleBooking.vehicleNew,
      lazy: async () => ({
        Component: (await import('./pages/vehicle-catalog-form-page')).VehicleCatalogFormPage,
      }),
    },
    {
      path: `${appRoutes.vehicleBooking.vehicles}/:id`,
      lazy: async () => ({
        Component: (await import('./pages/vehicle-catalog-form-page')).VehicleCatalogFormPage,
      }),
    },
    {
      path: appRoutes.vehicleBooking.drivers,
      lazy: async () => ({
        Component: (await import('./pages/driver-list-page')).DriverListPage,
      }),
    },
    {
      path: appRoutes.vehicleBooking.driverNew,
      lazy: async () => ({
        Component: (await import('./pages/driver-catalog-form-page')).DriverCatalogFormPage,
      }),
    },
    {
      path: `${appRoutes.vehicleBooking.drivers}/:id`,
      lazy: async () => ({
        Component: (await import('./pages/driver-catalog-form-page')).DriverCatalogFormPage,
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
