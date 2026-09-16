import { Download, Inbox, Search } from 'lucide-react'
import { useMemo, useState } from 'react'

import { downloadFile } from '@/core/api'
import { Button } from '@/shared/ui/button'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'
import type { ListParams } from '@/shared/types/api'

import { MyTripCard } from '../components/my-trip-card'
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
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
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
        //  `items-stretch` (mặc định của grid) chứ KHÔNG `items-start`: thẻ tự kéo
        //  cao bằng nhau nên cụm nút của cả hàng nằm trên một đường, mắt quét một
        //  lượt là xong. `items-start` cho mỗi thẻ cao theo nội dung — hàng nút
        //  nhấp nhô theo độ dài mục đích chuyến.
        //  `grid-cols-1` phải khai TƯỜNG MINH: thiếu nó thì ở khổ hẹp lưới chạy
        //  một cột `auto` — cột giãn theo nội dung dài nhất, `truncate` mất tác
        //  dụng và cả trang sinh thanh cuộn ngang. `grid-cols-1` là
        //  `minmax(0, 1fr)`, tức cột ĐƯỢC PHÉP co nhỏ hơn nội dung.
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {trips.map((trip) => (
            <MyTripCard key={trip.id} trip={trip} />
          ))}
        </div>
      )}
    </PageContainer>
  )
}
