import { Car, Stamp } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'

import type { ReportCatalogEntry } from './report-catalog'

/** Nhóm HÀNH CHÍNH của danh mục báo cáo (phase 05) — Đặt xe · Đóng dấu (Văn bản · Phê duyệt ở `report-catalog-document.ts`). */
export const ADMIN_REPORT_CATALOG: ReportCatalogEntry[] = [
  {
    label: 'Báo cáo đặt xe',
    description: 'Chuyến hoàn thành, tỷ lệ từ chối/hủy, chi phí, thời gian duyệt — theo xe, tài xế, bộ phận.',
    path: appRoutes.report.vehicleBooking,
    sourcePath: appRoutes.vehicleBooking.requests,
    icon: Car,
    //  ReportKey.VEHICLE_BOOKING (backend) = 9.
    key: 9,
    entity: 'vehicle_booking',
    group: 'Hành chính',
    endpoint: '/api/vehicle-bookings/summary',
    overviewKpis: ['requests', 'reject_cancel_rate'],
    load: async () => (await import('../pages/vehicle-booking-report-page')).VehicleBookingReportPage,
  },
  {
    label: 'Báo cáo đóng dấu',
    description:
      'Đề nghị, đã đóng dấu, tỷ lệ từ chối, thời gian duyệt và thời gian duyệt → đóng dấu — theo công ty, loại dấu.',
    path: appRoutes.report.sealRequest,
    sourcePath: appRoutes.approvalSeal.requests,
    icon: Stamp,
    //  ReportKey.SEAL_REQUEST (backend) = 10.
    key: 10,
    entity: 'seal_request',
    group: 'Hành chính',
    endpoint: '/api/seal-requests/summary',
    overviewKpis: ['requests', 'completed'],
    load: async () => (await import('../pages/seal-request-report-page')).SealRequestReportPage,
  },
]
