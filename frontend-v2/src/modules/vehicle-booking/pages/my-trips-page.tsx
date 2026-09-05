import { Inbox, MapPin } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'

import { BookingWorkflowActions } from '../components/booking-workflow-actions'
import { BookingStatusBadge, DriverStatusBadge } from '../components/status-pill'
import { useVehicleBookings } from '../hooks/use-vehicle-bookings'
import { BOOKING_STATUS, DRIVER_STATUS, type VehicleBooking } from '../types/vehicle-booking'

//  Ba nhóm theo bước của tài xế — chỉ những chuyến đang cần tài xế xử lý.
const GROUPS: { key: number; title: string }[] = [
  { key: DRIVER_STATUS.waiting, title: 'Chờ bạn nhận' },
  { key: DRIVER_STATUS.accepted, title: 'Đã nhận — chờ khởi hành' },
  { key: DRIVER_STATUS.ongoing, title: 'Đang đi' },
]

/**
 * "Chuyến của tôi" — màn gọn cho TÀI XẾ: chỉ chuyến ĐƯỢC PHÂN cho chính mình
 * (backend lọc bằng `?mine=1`), nhóm theo bước, thao tác Nhận / Bắt đầu / Hoàn tất
 * ngay trên thẻ. Người không phải tài xế mở ra sẽ thấy rỗng.
 */
export function MyTripsPage() {
  const { data, isPending } = useVehicleBookings({
    mine: 1,
    status: BOOKING_STATUS.dispatched,
    page_size: 100,
  })
  const trips = (data?.items ?? []) as VehicleBooking[]

  return (
    <PageContainer className="w-full">
      <PageHeader
        title="Chuyến của tôi"
        description="Các chuyến xe được phân cho bạn — nhận, bắt đầu và hoàn tất tại đây."
      />

      {isPending ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      ) : trips.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed py-14 text-muted-foreground">
          <Inbox className="size-8" />
          <p className="text-sm">Bạn chưa có chuyến nào được phân.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {GROUPS.map((group) => {
            const rows = trips.filter((t) => t.driver_status === group.key)
            if (rows.length === 0) return null
            return (
              <section key={group.key} className="flex flex-col gap-3">
                <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  {group.title} ({rows.length})
                </h3>
                {/* Màn rộng: xếp thẻ chuyến thành lưới nhiều cột thay vì một cột dài. */}
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {rows.map((trip) => (
                    <TripCard key={trip.id} trip={trip} />
                  ))}
                </div>
              </section>
            )
          })}
        </div>
      )}
    </PageContainer>
  )
}

function TripCard({ trip }: { trip: VehicleBooking }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Link
            to={appRoutes.vehicleBooking.detail(trip.id)}
            className="font-semibold text-foreground hover:underline"
          >
            {trip.code}
          </Link>
          <BookingStatusBadge status={trip.status} />
          <DriverStatusBadge status={trip.driver_status} />
        </div>
        <span className="text-xs text-muted-foreground">{trip.request_type_label}</span>
      </div>

      <div className="mt-2 flex items-start gap-1.5 text-sm">
        <MapPin className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
        <span>
          {trip.start_location || '—'} <span className="text-muted-foreground">→</span>{' '}
          {trip.end_location || '—'}
        </span>
      </div>
      <div className="mt-1 text-xs text-muted-foreground">
        {trip.start_time || '—'} → {trip.end_time || '—'}
      </div>
      {trip.assigned_vehicle_label && (
        <div className="mt-1 text-xs text-muted-foreground">Xe: {trip.assigned_vehicle_label}</div>
      )}
      {trip.purpose && <div className="mt-1 text-sm">{trip.purpose}</div>}

      <div className="mt-3">
        {/* Tài xế không điều phối — truyền no-op cho nút điều phối (không hiện với tài xế). */}
        <BookingWorkflowActions booking={trip} onDispatch={() => undefined} />
      </div>
    </div>
  )
}
