import viLocale from '@fullcalendar/core/locales/vi'
import dayGridPlugin from '@fullcalendar/daygrid'
import FullCalendar from '@fullcalendar/react'
import { MapPin, User, UserCog } from 'lucide-react'
import { useMemo, useState, type CSSProperties } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { CarBookingIcon, DeliveryBookingIcon } from '../components/booking-type-icons'
import type { TimelineEvent } from '../api/vehicle-booking-timeline-api'
import { useVehicleBookingTimeline } from '../hooks/use-vehicle-booking-timeline'
import {
  BOOKING_STATUS_LABELS,
  BOOKING_STATUS_TONE,
  REQUEST_TYPE,
  REQUEST_TYPE_LABELS,
} from '../types/vehicle-booking'

type Tone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

/** Lớp màu thẻ sự kiện theo trạng thái phiếu — viền trái + nền mờ (sáng & tối). */
const TONE_CLASSES: Record<Tone, string> = {
  neutral: 'border-l-muted-foreground/50 bg-muted/60 text-foreground',
  info: 'border-l-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300',
  success: 'border-l-green-500 bg-green-50 text-green-700 dark:bg-green-950/40 dark:text-green-300',
  warning: 'border-l-amber-500 bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300',
  danger: 'border-l-red-500 bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300',
}

/** '2026-09-10T05:00' -> '05:00'; không có giờ -> ''. */
function timeOf(startTime: string): string {
  const i = startTime.indexOf('T')
  return i >= 0 ? startTime.slice(i + 1, i + 6) : ''
}

/** Ngày local (theo múi trình duyệt) -> 'yyyy-mm-dd'. */
function toYmd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** '2026-09-01T…' -> '2026-09-01'; rỗng -> ''. */
function dateOf(iso: string): string {
  return iso ? iso.slice(0, 10) : ''
}

/** 'yyyy-mm-dd' + 1 ngày — mốc `end` của FullCalendar (all-day) là LOẠI TRỪ. */
function nextDay(ymd: string): string {
  const d = new Date(`${ymd}T00:00:00`)
  d.setDate(d.getDate() + 1)
  return toYmd(d)
}

/** Thẻ một chuyến xe trên lịch — icon loại, giờ, mục đích, người tạo, tài xế/xe, điểm đến. */
function EventCard({ ev }: { ev: TimelineEvent }) {
  const tone = BOOKING_STATUS_TONE[ev.status] ?? 'neutral'
  const isDelivery = ev.request_type === REQUEST_TYPE.delivery
  const time = timeOf(ev.start_time)
  const title = ev.purpose || ev.request_type_label
  const dispatchLabel =
    [ev.assigned_driver_label, ev.assigned_vehicle_label].filter(Boolean).join(' · ') || 'Chưa điều phối'
  const location = ev.end_location || ev.start_location || ''

  return (
    <div
      className={cn(
        'flex h-full w-full flex-col overflow-hidden rounded border-l-[3px] px-1.5 py-1 transition-all',
        'hover:-translate-y-px hover:shadow-md',
        TONE_CLASSES[tone],
      )}
    >
      <div className="flex items-center gap-1 truncate text-xs font-medium">
        {isDelivery ? (
          <DeliveryBookingIcon className="size-3.5 shrink-0" />
        ) : (
          <CarBookingIcon className="size-3.5 shrink-0" />
        )}
        {time && <span className="shrink-0 font-semibold tabular-nums">{time}</span>}
        <span className="truncate">{title}</span>
      </div>
      <div className="mt-0.5 flex flex-col gap-0.5 text-[10px] leading-tight opacity-90">
        {ev.requester && (
          <span className="flex items-center gap-1 truncate">
            <User className="size-3 shrink-0" />
            <span className="truncate">{ev.requester}</span>
          </span>
        )}
        <span className="flex items-center gap-1 truncate">
          <UserCog className="size-3 shrink-0" />
          <span className="truncate">{dispatchLabel}</span>
        </span>
        {location && (
          <span className="flex items-center gap-1 truncate opacity-80">
            <MapPin className="size-3 shrink-0" />
            <span className="truncate">{location}</span>
          </span>
        )}
      </div>
    </div>
  )
}

/**
 * Trang TIMELINE — lịch tháng các chuyến xe (FullCalendar). Mỗi phiếu là một thẻ
 * tô màu theo trạng thái; bấm vào mở trang chi tiết. Đổi tháng thì nạp lại đúng
 * khoảng hiển thị. Phạm vi dữ liệu bó theo quyền người xem (backend `apply_scope`).
 */
export function VehicleBookingTimelinePage() {
  const navigate = useNavigate()
  //  Khoảng hiển thị của lịch — FullCalendar báo qua `datesSet` mỗi lần đổi tháng.
  const [range, setRange] = useState<{ date_from: string; date_to: string } | null>(null)
  //  Bộ lọc trên hàng tiêu đề (lọc phía client trên dữ liệu đã tải của lịch).
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const { data, isFetching } = useVehicleBookingTimeline(range)

  const events = useMemo(() => {
    const items = (data?.items ?? []).filter((ev) => {
      if (typeFilter !== 'all' && ev.request_type !== Number(typeFilter)) return false
      if (statusFilter !== 'all' && ev.status !== Number(statusFilter)) return false
      return true
    })
    return items.map((ev) => {
      //  Chuyến kéo dài NHIỀU ngày (giờ kết thúc sang ngày khác) → một thẻ liên tiếp
      //  trải hết quá trình. `end` all-day là mốc LOẠI TRỪ nên +1 ngày để phủ ngày cuối.
      const endDate = dateOf(ev.end_time)
      const multiDay = Boolean(endDate) && endDate > ev.event_date
      return {
        id: String(ev.id),
        title: ev.purpose || ev.request_type_label,
        start: ev.event_date,
        end: multiDay ? nextDay(endDate) : undefined,
        allDay: true,
        //  Sắp trong ngày theo giờ khởi hành (chuỗi 'HH:mm', rỗng đứng trước) —
        //  `eventOrder="order"` đọc khóa này trong extendedProps.
        extendedProps: { ev, order: timeOf(ev.start_time) },
      }
    })
  }, [data, typeFilter, statusFilter])

  //  Biến FullCalendar theo token giao diện (v6 tự nhúng CSS, chỉ cần đặt biến).
  const fcTheme = {
    '--fc-border-color': 'var(--border)',
    '--fc-page-bg-color': 'transparent',
    '--fc-neutral-bg-color': 'var(--muted)',
    '--fc-today-bg-color': 'color-mix(in oklab, var(--primary) 8%, transparent)',
    '--fc-button-bg-color': 'var(--primary)',
    '--fc-button-border-color': 'var(--primary)',
    '--fc-button-text-color': 'var(--primary-foreground)',
    '--fc-button-hover-bg-color': 'color-mix(in oklab, var(--primary) 88%, black)',
    '--fc-button-hover-border-color': 'color-mix(in oklab, var(--primary) 88%, black)',
    '--fc-button-active-bg-color': 'color-mix(in oklab, var(--primary) 80%, black)',
    '--fc-button-active-border-color': 'color-mix(in oklab, var(--primary) 80%, black)',
  } as CSSProperties

  return (
    <PageContainer>
      <PageHeader
        title="Lịch đặt xe"
        description="Lịch các chuyến xe theo dòng thời gian — bấm vào một chuyến để xem chi tiết."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {/*  Bộ lọc trên hàng tiêu đề: loại đặt xe · trạng thái. */}
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="h-9 w-40 text-xs">
                <SelectValue placeholder="Loại đặt xe" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tất cả loại</SelectItem>
                <SelectItem value={String(REQUEST_TYPE.car)}>{REQUEST_TYPE_LABELS[REQUEST_TYPE.car]}</SelectItem>
                <SelectItem value={String(REQUEST_TYPE.delivery)}>
                  {REQUEST_TYPE_LABELS[REQUEST_TYPE.delivery]}
                </SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="h-9 w-44 text-xs">
                <SelectValue placeholder="Trạng thái" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tất cả trạng thái</SelectItem>
                {Object.entries(BOOKING_STATUS_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        }
      />

      <Card
        className="p-2 sm:p-4 [&_.fc-col-header-cell-cushion]:text-muted-foreground [&_.fc-daygrid-day-number]:text-muted-foreground [&_.fc-toolbar-title]:text-lg [&_.fc-toolbar-title]:font-semibold [&_.fc-toolbar-title]:first-letter:uppercase [&_.fc_a]:!text-inherit"
        style={fcTheme}
        aria-busy={isFetching}
      >
        <FullCalendar
          plugins={[dayGridPlugin]}
          initialView="dayGridMonth"
          locale={viLocale}
          height="auto"
          headerToolbar={{ left: 'title', center: '', right: 'prev,next today' }}
          buttonText={{ today: 'Hôm nay' }}
          firstDay={0}
          dayMaxEvents={4}
          fixedWeekCount={false}
          eventOrder="order"
          events={events}
          //  Bỏ nền/viền mặc định của FC, để `EventCard` tự tô — giống mẫu tham khảo.
          eventClassNames="!border-none !bg-transparent !shadow-none !p-0 cursor-pointer"
          eventContent={(arg) => <EventCard ev={arg.event.extendedProps.ev as TimelineEvent} />}
          eventClick={(arg) => navigate(appRoutes.vehicleBooking.detail(Number(arg.event.id)))}
          datesSet={(arg) => {
            //  arg.start/end phủ trọn lưới tháng (kể cả ngày tràn) — dùng đúng khoảng đó.
            const to = new Date(arg.end)
            to.setDate(to.getDate() - 1) // `end` là mốc loại trừ
            setRange({ date_from: toYmd(arg.start), date_to: toYmd(to) })
          }}
        />
      </Card>
    </PageContainer>
  )
}
