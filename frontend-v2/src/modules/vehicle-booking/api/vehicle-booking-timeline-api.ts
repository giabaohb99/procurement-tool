import { apiGet } from '@/core/api'

import type { VehicleBooking } from '../types/vehicle-booking'

/**
 * Một chuyến xe trên lịch Timeline — đúng dạng phiếu đã nối nhãn (như danh sách),
 * kèm `event_date` (yyyy-mm-dd) là NGÀY hiển thị trên lịch (ngày khởi hành, lùi về
 * ngày tạo nếu chưa có giờ khởi hành).
 */
export interface TimelineEvent extends VehicleBooking {
  event_date: string
}

/** Khoảng hiển thị của lịch (yyyy-mm-dd) — FullCalendar báo mỗi lần đổi tháng. */
export interface TimelineParams {
  date_from: string
  date_to: string
}

export const vehicleBookingTimelineApi = {
  getTimeline: (params: TimelineParams) =>
    apiGet<{ items: TimelineEvent[] }>('/api/vehicle-bookings/timeline', { params }),
}
