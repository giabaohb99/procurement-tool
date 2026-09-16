import viLocale from '@fullcalendar/core/locales/vi'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import timeGridPlugin from '@fullcalendar/timegrid'
import FullCalendar from '@fullcalendar/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useSetUrlParams } from '@/shared/hooks/use-url-param-state'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { parseLocalDate } from '@/shared/utils/format-date'
import { BookingCalendarChip } from '../components/booking-calendar-chip'
import { BookingCalendarDayHeader } from '../components/booking-calendar-day-header'
import { BookingCalendarToolbar } from '../components/booking-calendar-toolbar'
import { CALENDAR_GRID_CLASSES, FC_THEME_VARS } from '../utils/calendar-theme'
import {
  isTimeGridView,
  modeFromView,
  viewFromMode,
  type CalendarViewType,
} from '../utils/calendar-views'
import { timeOf } from '../utils/booking-time-format'
import type { TimelineEvent } from '../api/vehicle-booking-timeline-api'
import { useVehicleBookingTimeline } from '../hooks/use-vehicle-booking-timeline'
import {
  BOOKING_STATUS_LABELS,
  REQUEST_TYPE,
  REQUEST_TYPE_LABELS,
} from '../types/vehicle-booking'

/** Ngày local (theo múi trình duyệt) -> 'yyyy-mm-dd'. */
function toYmd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** '2026-09-01T…' -> '2026-09-01'; rỗng -> ''. */
function dateOf(iso: string): string {
  return iso ? iso.slice(0, 10) : ''
}

/**
 * Date -> 'yyyy-MM-ddTHH:mm' theo giờ ĐỊA PHƯƠNG, đúng khuôn `start_time` backend.
 *
 * KHÔNG dùng `toISOString()`: hàm đó đổi sang UTC, nên 08:00 giờ Việt Nam ra
 * '01:00Z' — phiếu mở ra lệch 7 tiếng.
 */
function toLocalIsoMinute(d: Date): string {
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${toYmd(d)}T${hh}:${mm}`
}

/** 'yyyy-mm-dd' + 1 ngày — mốc `end` của FullCalendar (all-day) là LOẠI TRỪ. */
function nextDay(ymd: string): string {
  const d = new Date(`${ymd}T00:00:00`)
  d.setDate(d.getDate() + 1)
  return toYmd(d)
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
  //  Thanh tiêu đề tự dựng nên phải tự giữ nhãn tháng + tự gọi API của lịch.
  const calendarRef = useRef<FullCalendar>(null)
  const [viewTitle, setViewTitle] = useState('')

  //  --- Chỗ đang xem nằm trong URL (`?mode=week&date=2026-08-23`) ---
  //  Để F5 / mở lại từ lịch sử trình duyệt / gửi link đều rơi đúng chỗ cũ.
  const [searchParams] = useSearchParams()
  const setUrlParams = useSetUrlParams()

  //  Đọc URL ĐÚNG MỘT LẦN lúc dựng màn: `initialView`/`initialDate` chỉ được
  //  FullCalendar ngó tới ở lần vẽ đầu, đổi về sau phải gọi API của lịch. Dùng
  //  `useState` có hàm khởi tạo chứ không tính thẳng trong thân component —
  //  tính thẳng thì mỗi lần vẽ lại ra một giá trị mới và React so ra prop đổi.
  const [initial] = useState(() => ({
    view: viewFromMode(searchParams.get('mode')),
    //  Sai dạng / ngày không có thật → `undefined` = FC tự mở ở hôm nay.
    date: parseLocalDate(searchParams.get('date')),
  }))
  const [view, setView] = useState<CalendarViewType>(initial.view)

  //  Chiều ngược: URL đổi mà không do lịch → kéo lịch theo.
  //
  //  Cần vì `initialView`/`initialDate` chỉ đọc một lần: bấm lại chính mục menu
  //  "Lịch đặt xe" lúc đang ở `?mode=day` sẽ về URL trống nhưng lịch VẪN nằm ở
  //  khám Ngày — URL nói một đằng, màn hình một nẻo, và cú F5 kế tiếp nhảy sang
  //  chỗ khác. Chạy nhánh này thì bấm lại menu = trở về mặc định (tháng này),
  //  và nút Back/Forward của trình duyệt cũng đi đúng.
  //
  //  Không sợ lặp vô tận: `changeView` làm `datesSet` chạy → ghi lại URL đúng
  //  bằng giá trị vừa đọc → lượt sau `isShowing` đúng nên không gọi gì nữa.
  useEffect(() => {
    const api = calendarRef.current?.getApi()
    if (!api) return
    const wantView = viewFromMode(searchParams.get('mode'))
    //  Thiếu `date` nghĩa là "hôm nay", không phải "giữ nguyên chỗ cũ".
    const wantDate = parseLocalDate(searchParams.get('date')) ?? new Date()
    const isShowing =
      api.view.type === wantView &&
      wantDate >= api.view.currentStart &&
      wantDate < api.view.currentEnd
    if (!isShowing) api.changeView(wantView, wantDate)
  }, [searchParams])

  const { can } = usePermission()
  const canCreate = can('vehicle_booking', 'create')

  const { data, isFetching } = useVehicleBookingTimeline(range)

  const events = useMemo(() => {
    const items = (data?.items ?? []).filter((ev) => {
      if (typeFilter !== 'all' && ev.request_type !== Number(typeFilter)) return false
      if (statusFilter !== 'all' && ev.status !== Number(statusFilter)) return false
      return true
    })
    return items.map((ev) => {
      //  Chuyến TRONG MỘT NGÀY → sự kiện CÓ GIỜ, để khám Ngày/Tuần xếp nó lên
      //  trục giờ (`start_time`/`end_time` là chuỗi ISO tới phút, đúng dạng FC cần).
      //
      //  Chuyến SANG NGÀY KHÁC → sự kiện "cả ngày", nằm ở dải *Cả ngày* trên đỉnh.
      //  Để nó lên trục giờ thì một chuyến 4 ngày thành cột màu cao vô tận chạy
      //  quá đáy khung, mà 40% dữ liệu là loại này nên cả khám Tuần bị chúng lấn.
      //  Google Calendar cũng dồn sự kiện nhiều ngày lên dải đó.
      //  `end` của sự kiện cả ngày là mốc LOẠI TRỪ → phải +1 ngày mới phủ hết ngày
      //  cuối; sự kiện có giờ thì `end` là mốc thật, KHÔNG cộng thêm.
      const startDate = dateOf(ev.start_time) || ev.event_date
      const endDate = dateOf(ev.end_time)
      const spansDays = Boolean(endDate) && endDate > startDate
      if (!ev.start_time || spansDays) {
        return {
          id: String(ev.id),
          title: ev.purpose || ev.request_type_label,
          start: startDate,
          end: spansDays ? nextDay(endDate) : undefined,
          allDay: true,
          extendedProps: { ev, order: timeOf(ev.start_time) },
        }
      }
      return {
        id: String(ev.id),
        title: ev.purpose || ev.request_type_label,
        start: ev.start_time,
        //  Thiếu giờ về thì để FC tự lấy thời lượng mặc định, đừng dựng `end` giả.
        end: ev.end_time || undefined,
        allDay: false,
        //  Sắp trong ngày theo giờ khởi hành (chuỗi 'HH:mm', rỗng đứng trước) —
        //  `eventOrder="order"` đọc khóa này trong extendedProps.
        extendedProps: { ev, order: timeOf(ev.start_time) },
      }
    })
  }, [data, typeFilter, statusFilter])

  return (
    //  `fill` — trang chiếm trọn chiều cao khung, lịch tự giãn lấp phần còn lại.
    //  Lề ngoài thu lại so với mặc định `p-4 lg:p-6`: chỗ tiết kiệm được dồn hết
    //  vào ô ngày, thứ duy nhất trên trang này cần diện tích.
    <PageContainer fill className="gap-3 p-3 lg:p-4">
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
        className={CALENDAR_GRID_CLASSES}
        style={FC_THEME_VARS}
        aria-busy={isFetching}
      >
        <BookingCalendarToolbar
          title={viewTitle}
          view={view}
          onViewChange={(next) => {
            //  Đổi khám qua API của lịch; `datesSet` sẽ tự cập nhật `view` +
            //  nhãn + khoảng nạp dữ liệu, nên không setState trùng ở đây.
            calendarRef.current?.getApi().changeView(next)
          }}
          onPrev={() => calendarRef.current?.getApi().prev()}
          onNext={() => calendarRef.current?.getApi().next()}
          onToday={() => calendarRef.current?.getApi().today()}
        />
        <FullCalendar
          ref={calendarRef}
          //  `interactionPlugin` là điều kiện để có `dateClick` — thiếu nó thì prop đó
          //  không tồn tại và TypeScript báo ngay ở chỗ khai.
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView={initial.view}
          initialDate={initial.date}
          locale={viLocale}
          //  Lấp trọn chiều cao thẻ → 6 hàng tuần CHIA ĐỀU nhau, không còn cảnh
          //  tuần nhiều chuyến cao gấp bốn tuần rỗng, và hết khoảng trắng dưới lịch.
          height="100%"
          //  Thanh tiêu đề dựng tay ở `BookingCalendarToolbar` — xem lý do trong
          //  chú thích của component đó.
          headerToolbar={false}
          firstDay={0}
          //  `true` = tự tính số chip vừa chiều cao ô thật rồi gom phần dôi vào
          //  "+N chuyến nữa" — đúng cách Google Calendar làm. Đặt số cứng thì màn
          //  cao vẫn chừa chỗ trống, màn thấp lại tràn. Chỉ có tác dụng ở khám Tháng.
          dayMaxEvents={true}
          //  --- Khám Ngày · Tuần (có trục giờ) ---
          //  Không ghim 0-24h: đội xe chạy sớm nhất ~04:00, muộn nhất ~23:00, mở
          //  trọn 24h thì hai đầu toàn khoảng trắng và phần giữa bị nén lại.
          slotMinTime="04:00:00"
          slotMaxTime="24:00:00"
          slotDuration="01:00:00"
          slotLabelFormat={{ hour: '2-digit', minute: '2-digit', hour12: false }}
          //  Giờ trên chip do chip tự vẽ rồi — tắt phần giờ mặc định của FC.
          displayEventTime={false}
          allDayText="Cả ngày"
          nowIndicator
          //  Cuộn tới đầu dải giờ khi mở màn. Mặc định của FC là `06:00`, mà lưới
          //  này bắt đầu từ `04:00` — để mặc định thì vừa mở đã mất hai tiếng đầu
          //  mà không có gì báo là đang bị cuộn.
          scrollTime="04:00:00"
          //  Chuyến ngắn (1 tiếng) ra khối ~18px, không đủ chỗ cho một dòng chữ
          //  nên giờ + mục đích bị cắt ngang. Ghim sàn 28px = đúng chiều cao chip
          //  ở khám Tháng, đọc được; đổi lại khối hơi cao hơn thời lượng thật.
          eventMinHeight={28}
          //  Mặc định vi của FC là "+ thêm 1" — nói rõ đơn vị cho đúng nghiệp vụ.
          moreLinkText={(n) => `+${n} chuyến nữa`}
          fixedWeekCount={false}
          eventOrder="order"
          //  Tiêu đề cột: khám Tháng giữ mặc định của locale ("CN · T2 · …").
          //  Hai khám có trục giờ chỉ lấy TÊN THỨ ở đây, con số ngày do
          //  `dayHeaderContent` dựng thành dòng thứ hai bên dưới.
          //
          //  `expandRows` KHAI RIÊNG TỪNG KHÁM, không khai chung:
          //  · Tháng — BẬT, để 6 hàng tuần chia đều hết chiều cao thẻ. Tắt là hàng
          //    co về chiều cao tự nhiên và chừa một mảng trắng dưới lịch.
          //  · Ngày/Tuần — TẮT, để mỗi giờ giữ đúng chiều cao ghim (xem
          //    `CALENDAR_GRID_CLASSES`) và phần dôi ra thì CUỘN. Bật thì 20 hàng
          //    giờ bị kéo/nén theo chiều cao cửa sổ: màn thấp ra hàng ~28px, chuyến
          //    một tiếng mỏng như sợi chỉ, mà cùng tệp đó mở trên màn cao lại khác.
          views={{
            dayGridMonth: { expandRows: true },
            timeGridDay: { dayHeaderFormat: { weekday: 'long' }, expandRows: false },
            timeGridWeek: { dayHeaderFormat: { weekday: 'short' }, expandRows: false },
          }}
          dayHeaderContent={(arg) =>
            //  Khám Tháng trả lại ĐÚNG CHỮ mặc định. KHÔNG trả `undefined` để
            //  "nhờ FC dựng mặc định": FC nhận đó là nội dung rỗng và hàng tiêu
            //  đề tháng mất sạch CN · T2 · … (đã dính lỗi này 16/09/2026).
            isTimeGridView(arg.view.type) ? (
              <BookingCalendarDayHeader
                weekday={arg.text}
                dayOfMonth={arg.date.getDate()}
                isToday={arg.isToday}
              />
            ) : (
              arg.text
            )
          }
          events={events}
          //  Bỏ nền/viền mặc định của FC, để chip tự tô.
          eventClassNames="!border-none !bg-transparent !shadow-none !p-0 cursor-pointer"
          eventContent={(arg) => (
            <BookingCalendarChip
              ev={arg.event.extendedProps.ev as TimelineEvent}
              //  Chip cao hết ô ở khám có trục giờ; dải "Cả ngày" trên đỉnh thì
              //  vẫn là chip cao cố định như khám Tháng.
              fillHeight={isTimeGridView(arg.view.type) && !arg.event.allDay}
            />
          )}
          eventClick={(arg) => navigate(appRoutes.vehicleBooking.detail(Number(arg.event.id)))}
          //  Gợi ý TẠO PHIẾU: chèn một dấu + vào ĐÁY ô ngày, chỉ sáng khi trỏ vào
          //  chỗ trống. Phải là PHẦN TỬ THẬT chứ không phải `::after` — Tailwind
          //  không sinh nổi glyph qua `content` ở đây (thử cả `content-['+']` lẫn
          //  `[content:'+']`, `getComputedStyle` đều trả `content: ""`).
          dayCellDidMount={(arg) => {
            if (!canCreate) return
            //  CHỈ khám Tháng. Khám Ngày/Tuần cũng có ô `daygrid` — đó là dải
            //  "Cả ngày" cao 26px — nên dấu + 20px chèn vào đó gần như lấp kín
            //  dải, mà chỗ tạo phiếu ở hai khám đó là khung giờ bên dưới.
            if (isTimeGridView(arg.view.type)) return
            const frame = arg.el.querySelector('.fc-daygrid-day-frame')
            if (!frame || frame.querySelector('[data-create-hint]')) return
            const hint = document.createElement('div')
            hint.dataset.createHint = ''
            hint.textContent = '+'
            //  Dấu trang trí — không có nó thì cây trợ năng mọc thêm 35 nút "+"
            //  và trình đọc màn hình đọc "cộng" 35 lần khi rà qua lịch.
            hint.setAttribute('aria-hidden', 'true')
            //  CỐ Ý không gán className ở đây: Tailwind quét MÃ NGUỒN, và lớp nằm
            //  trong chuỗi ghép bằng `+` của tệp này thì nó bỏ qua (đã kiểm: không
            //  sinh luật nào cho `group-hover:`). Toàn bộ dáng của dấu + khai ở
            //  `CALENDAR_GRID_CLASSES` dưới dạng `[&_[data-create-hint]]:…`.
            frame.appendChild(hint)
          }}
          //  Bấm SỐ NGÀY → mở đúng ngày đó ở khám Ngày (kiểu Google Calendar).
          //  `navLinks` biến số ngày thành liên kết; không khai `navLinkDayClick`
          //  thì FC nhảy sang `dayGridDay` (không trục giờ), nên chỉ định tay.
          navLinks
          navLinkDayClick={(date) => {
            calendarRef.current?.getApi().changeView('timeGridDay', date)
          }}
          //  Bấm vào Ô NGÀY (hoặc khung giờ) → mở form tạo phiếu, điền sẵn giờ vừa
          //  chỉ. Khám Tháng chỉ cho ra ngày (`allDay`) nên mặc định 08:00 — đầu
          //  giờ làm; khám Ngày/Tuần thì lấy đúng khung giờ người dùng bấm.
          dateClick={(arg) => {
            if (!canCreate) return
            const start = arg.allDay ? `${arg.dateStr.slice(0, 10)}T08:00` : toLocalIsoMinute(arg.date)
            navigate(`${appRoutes.vehicleBooking.new}?start=${encodeURIComponent(start)}`)
          }}
          datesSet={(arg) => {
            //  arg.start/end phủ trọn lưới tháng (kể cả ngày tràn) — dùng đúng khoảng đó.
            const to = new Date(arg.end)
            to.setDate(to.getDate() - 1) // `end` là mốc loại trừ
            setRange({ date_from: toYmd(arg.start), date_to: toYmd(to) })
            setViewTitle(arg.view.title)
            setView(arg.view.type as CalendarViewType)

            //  Ghi chỗ đang xem vào URL. `datesSet` chạy sau MỌI lần đổi khám /
            //  bấm ‹ › / bấm số ngày, nên đây là chỗ duy nhất phải ghi.
            //
            //  Mốc ngày lấy `view.currentStart` (đầu kỳ THẬT), KHÔNG lấy
            //  `arg.start`: lưới tháng 9 bắt đầu từ 30/08 nên ghi `arg.start` là
            //  F5 xong nhảy về tháng 8.
            const mode = modeFromView(arg.view.type)
            const date = toYmd(arg.view.currentStart)
            //  Chỉ ghi khi KHÁC — `setSearchParams` mỗi lần vẽ là một vòng lặp
            //  render vô ích (URL đổi → vẽ lại → FC báo `datesSet` → …).
            if (searchParams.get('mode') !== mode || searchParams.get('date') !== date) {
              //  Một lượt cho cả hai param: gọi hai setter liên tiếp thì lần sau
              //  đọc URL cũ và ghi đè lần trước — xem `useSetUrlParams`.
              setUrlParams({ mode, date })
            }
          }}
        />
      </Card>
    </PageContainer>
  )
}
