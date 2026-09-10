import { Download, Inbox, MapPin, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { downloadFile } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'
import type { ListParams } from '@/shared/types/api'

import { BookingWorkflowActions } from '../components/booking-workflow-actions'
import { BookingStatusBadge, DriverStatusBadge } from '../components/status-pill'
import { useVehicleBookings } from '../hooks/use-vehicle-bookings'
import { BOOKING_STATUS, type VehicleBooking } from '../types/vehicle-booking'

/** Ngày local → 'yyyy-mm-dd'. */
function toYmd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Khoảng mặc định: 30 ngày gần nhất. */
function defaultRange(): { from: string; to: string } {
  const to = new Date()
  const from = new Date()
  from.setDate(to.getDate() - 29)
  return { from: toYmd(from), to: toYmd(to) }
}

/**
 * "Chuyến của tôi" — chỉ chuyến ĐƯỢC PHÂN cho chính mình (backend lọc `?mine=1`).
 * Thẻ xếp phẳng, MỚI NHẤT lên trên; có bộ lọc thời gian (30 ngày mặc định) + tìm
 * kiếm; bấm vào thẻ mở trang chi tiết; thao tác Nhận / Bắt đầu / Hoàn tất trên thẻ.
 */
export function MyTripsPage() {
  const navigate = useNavigate()
  const [range, setRange] = useState(defaultRange)
  const [search, setSearch] = useState('')

  const params: ListParams = {
    mine: 1,
    status: BOOKING_STATUS.dispatched,
    page_size: 100,
  }
  if (search.trim()) params.search = search.trim()
  if (range.from) params.created_at_from = range.from
  if (range.to) params.created_at_to = range.to

  const { data, isPending } = useVehicleBookings(params)

  //  Xuất Excel đúng bộ lọc đang xem (mine + đã điều phối + tìm kiếm + khoảng ngày).
  const handleExport = async () => {
    const q = new URLSearchParams({ mine: '1', status: String(BOOKING_STATUS.dispatched) })
    if (search.trim()) q.set('search', search.trim())
    if (range.from) q.set('created_at_from', range.from)
    if (range.to) q.set('created_at_to', range.to)
    await downloadFile(`/api/vehicle-bookings/export/xlsx?${q.toString()}`, 'chuyen-cua-toi.xlsx')
  }
  //  Mới nhất lên trên (id tăng theo thời gian tạo — chưa lộ `updated_at` ở API danh sách).
  const trips = useMemo(
    () => [...((data?.items ?? []) as VehicleBooking[])].sort((a, b) => b.id - a.id),
    [data],
  )

  return (
    <PageContainer className="w-full">
      <PageHeader
        title="Chuyến của tôi"
        description="Các chuyến xe được phân cho bạn — nhận, bắt đầu và hoàn tất tại đây."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative min-w-56">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="h-9 pl-9 text-xs"
                placeholder="Tìm theo mã, mục đích, điểm đi/đến…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <DateRangePicker
              from={range.from}
              to={range.to}
              placeholder="Khoảng thời gian…"
              onChange={(from, to) => setRange({ from, to })}
            />
            <Button variant="outline" size="sm" onClick={() => void handleExport()}>
              <Download className="mr-1.5 size-4" />
              Xuất Excel
            </Button>
          </div>
        }
      />

      {isPending ? (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      ) : trips.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed py-14 text-muted-foreground">
          <Inbox className="size-8" />
          <p className="text-sm">Không có chuyến nào khớp bộ lọc.</p>
        </div>
      ) : (
        <div className="grid items-start gap-3 md:grid-cols-2 xl:grid-cols-3">
          {trips.map((trip) => (
            <TripCard key={trip.id} trip={trip} onOpen={() => navigate(appRoutes.vehicleBooking.detail(trip.id))} />
          ))}
        </div>
      )}
    </PageContainer>
  )
}

function TripCard({ trip, onOpen }: { trip: VehicleBooking; onOpen: () => void }) {
  return (
    //  Bấm cả thẻ → chi tiết; cụm nút thao tác chặn nổi bọt để không mở trang.
    <div
      role="button"
      tabIndex={0}
      onClick={onOpen}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onOpen()
        }
      }}
      className="cursor-pointer rounded-lg border bg-card p-4 transition-colors hover:border-primary/50 hover:bg-accent/40"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-foreground">{trip.code}</span>
          <BookingStatusBadge status={trip.status} driverStatus={trip.driver_status} />
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

      {/*  Khoảng cách các nút ~16px theo chiều ngang (`gap-4`); chặn nổi bọt để bấm nút
          không mở trang chi tiết. */}
      <div className="mt-3 flex flex-wrap items-center gap-4" onClick={(e) => e.stopPropagation()}>
        <BookingWorkflowActions booking={trip} onDispatch={() => undefined} />
      </div>
    </div>
  )
}
