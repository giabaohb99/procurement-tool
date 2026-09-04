import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronDown, ChevronLeft, ChevronRight, Plus, Search } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { Calendar } from '@/shared/ui/calendar'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { RoomTimelineGrid } from '../components/room-timeline-grid'
import { RoomSectionTabs } from '../components/room-section-tabs'
import {
  useMeetingRooms,
  useRescheduleRoomBooking,
  useRoomBookings,
} from '../hooks/use-room'
import { parseLocalDate } from '@/shared/utils/format-date'
import { matchesVietnamese } from '@/shared/utils/vn-text'
import { addDays, toISODate } from '../utils/calendar-grid'
import { blockingOnly, formatSlotHour } from '../utils/room-calendar-grid'
import { toApiTime } from '../utils/room-time'

/**
 * LỊCH ĐẶT PHÒNG — «hôm nay phòng nào còn trống».
 *
 * Lưới xếp **mỗi phòng một HÀNG, giờ chạy ngang** — xem `RoomTimelineGrid` về
 * lý do đảo trục (20 phòng thì bản cột dọc rộng 4.500px).
 *
 * Chỉ có chế độ **NGÀY**, cố ý: một ngày làm việc đã chiếm gần trọn bề ngang,
 * nhân bảy lần thì mỗi cuộc họp còn vài pixel. Muốn nhìn xa hơn một ngày thì tab
 * «Phiếu đặt phòng» có bộ lọc theo phòng và khoảng thời gian.
 *
 * Ngày đang xem nằm trên URL (`?date=`) để dán link cho nhau được — cùng cách
 * làm với Lịch nghỉ.
 */
export function RoomCalendarPage() {
  const navigate = useNavigate()
  const { can } = usePermission()

  const [dateParam, setDateParam] = useUrlParamState('date', toISODate(new Date()))
  const [openCalendar, setOpenCalendar] = useState(false)
  const day = useMemo(() => new Date(`${dateParam}T00:00:00`), [dateParam])

  const { data: roomData } = useMeetingRooms()
  const allRooms = useMemo(() => roomData?.items ?? [], [roomData])

  //  Lọc phòng ngay trên lưới. Bốn phòng thì không cần, nhưng hai chục phòng
  //  (khách hỏi 04/09/2026) thì cuộn dọc tìm đúng «Tầng 3» là việc hằng ngày —
  //  và ô này rẻ hơn nhiều so với dựng cây địa điểm.
  const [roomQuery, setRoomQuery] = useUrlParamState('room', '')
  const rooms = useMemo(
    //  So BỎ DẤU, cùng luật với hộp chọn phòng — xem `matchesVietnamese`.
    () => allRooms.filter((r) => matchesVietnamese([r.name, r.code, r.location, r.equipment], roomQuery)),
    [allRooms, roomQuery],
  )

  //  Hỏi đúng khoảng của NGÀY đang xem: `from_time`/`to_time` lọc theo GIAO
  //  NHAU nên cuộc họp vắt qua nửa đêm vẫn lọt vào.
  const params = useMemo(
    () => ({
      page: 1,
      page_size: 200,
      from_time: toApiTime(`${dateParam}T00:00`),
      to_time: toApiTime(`${dateParam}T23:59`),
    }),
    [dateParam],
  )
  const reschedule = useRescheduleRoomBooking()
  const { data, isLoading } = useRoomBookings(params)
  const bookings = useMemo(() => data?.items ?? [], [data])
  //  Đếm theo phiếu ĐANG GIỮ phòng, không đếm cả nháp/hủy — con số này đứng
  //  cạnh tên ngày nên nó phải khớp với thứ người dùng nhìn thấy trên lưới.
  const heldCount = useMemo(() => blockingOnly(bookings).length, [bookings])

  const shift = (days: number) => setDateParam(toISODate(addDays(day, days)))

  return (
    <PageContainer fill>
      <PageHeader
        title="Lịch đặt phòng"
        description="Phòng nào đang bận, ai giữ, tới mấy giờ. Bấm vào ô trống để đặt ngay."
        actions={
          can('room_booking', 'create') ? (
            <Button onClick={() => navigate(appRoutes.hr.roomBookingNew)}>
              <Plus className="size-4" />
              Đặt phòng
            </Button>
          ) : undefined
        }
      />

      <RoomSectionTabs />

      {/*  ⚠️ KHÔNG `flex-1`: bốn phòng thì lưới cao 210px, mà thẻ giãn hết
           khung là chừa một hộp rỗng cả nghìn pixel bên dưới (khách chụp lại
           04/09/2026). `max-h-full` để hai chục phòng vẫn cuộn trong thẻ chứ
           không đẩy cả trang dài ra. */}
      <Card className="flex min-h-0 w-full min-w-0 max-h-full flex-col overflow-hidden p-0">
        {/*  THANH CÔNG CỤ — mọi phần tử cao ĐÚNG 32px và cùng một đường tim.
             Bản đầu trộn ba chiều cao (nút 32px · khối ngày hai dòng 36px · ô
             lọc 32px) nên hàng gãy làm ba mức, nhìn lệch dù từng cụm đều đúng.
             Con số «lượt giữ phòng» tách khỏi nút ngày thành chip riêng chính
             vì nó là thứ làm nút đó cao hơn mọi thứ khác.

             ⚠️ CHÚ GIẢI bên TRÁI, cụm điều khiển bên PHẢI (khách chốt
             04/09/2026). Ngược với thói quen thường thấy, nhưng đây là màn ĐỌC:
             chú giải màu là thứ phải nắm trước khi hiểu lưới bên dưới, còn nút
             điều hướng thì chỉ tìm tới khi đã muốn đổi ngày. */}
        <div className="flex shrink-0 flex-wrap items-center gap-2 border-b px-3 py-2">
          <div className="flex h-8 items-center gap-3 border-r pr-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-1 rounded-sm bg-emerald-500" /> Đã duyệt
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-1 rounded-sm bg-amber-500" /> Chờ duyệt
            </span>
            <span className="flex items-center gap-1.5">
              <span className="size-3 rounded-sm bg-muted" /> Ngoài giờ làm
            </span>
          </div>

          <div className="ml-auto flex flex-wrap items-center gap-2">
            <span className="flex h-8 items-center rounded-md bg-muted px-2.5 text-xs text-muted-foreground tabular-nums">
              {heldCount} lượt giữ ·{' '}
              {rooms.length === allRooms.length
                ? `${allRooms.length} phòng`
                : `${rooms.length}/${allRooms.length} phòng`}
            </span>

            {/*  Chỉ dựng ô lọc khi danh sách đủ dài để phải lọc — công ty bốn
                 phòng mà bày thêm một ô tìm là thêm thứ để đọc mà không dùng tới. */}
            {allRooms.length > 6 && (
              <div className="relative">
                <Search className="absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="h-8 w-52 pl-8"
                  placeholder="Lọc phòng, tầng, thiết bị…"
                  aria-label="Lọc phòng"
                  value={roomQuery}
                  onChange={(e) => setRoomQuery(e.target.value)}
                />
              </div>
            )}

            {/*  TÊN NGÀY là nút mở lịch — gộp hai thứ vốn lặp nhau: bản đầu có
                 cả dòng «Thứ Sáu, 04/09/2026» LẪN một ô `<input type="date">`
                 ghi đúng ngày đó ngay bên cạnh. Ô ngày gốc của trình duyệt còn
                 mỗi hệ điều hành một kiểu và trên Windows hiện `mm/dd/yyyy`
                 trong khi cả hệ dùng `dd/mm/yyyy` — xem `shared/ui/date-picker.tsx`. */}
            <Popover open={openCalendar} onOpenChange={setOpenCalendar}>
              <PopoverTrigger asChild>
                <Button
                  variant="ghost"
                  className="h-8 gap-1.5 px-2 text-base font-semibold"
                  aria-label="Chọn ngày xem lịch"
                >
                  {day.toLocaleDateString('vi-VN', {
                    weekday: 'long',
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                  })}
                  <ChevronDown className="size-4 text-muted-foreground" />
                </Button>
              </PopoverTrigger>
              <PopoverContent align="end" className="w-auto p-0">
                <Calendar
                  mode="single"
                  selected={parseLocalDate(dateParam) ?? undefined}
                  defaultMonth={parseLocalDate(dateParam) ?? undefined}
                  onSelect={(picked) => {
                    if (!picked) return
                    setDateParam(toISODate(picked))
                    setOpenCalendar(false)
                  }}
                />
              </PopoverContent>
            </Popover>

            {/*  Ba nút dính liền thành một cụm: lùi · hôm nay · tiến là MỘT thao
                 tác điều hướng, tách rời ra thì mắt phải tìm lại từng nút. */}
            <div className="flex h-8 items-center rounded-md border">
              <Button
                variant="ghost"
                size="icon"
                className="size-8 rounded-r-none"
                aria-label="Ngày trước"
                onClick={() => shift(-1)}
              >
                <ChevronLeft className="size-4" />
              </Button>
              <Button
                variant="ghost"
                className="h-8 rounded-none border-x px-3 text-sm"
                onClick={() => setDateParam(toISODate(new Date()))}
              >
                Hôm nay
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className="size-8 rounded-l-none"
                aria-label="Ngày sau"
                onClick={() => shift(1)}
              >
                <ChevronRight className="size-4" />
              </Button>
            </div>
          </div>
        </div>

        {isLoading ? (
          <p className="p-6 text-sm text-muted-foreground">Đang tải lịch…</p>
        ) : (
          <RoomTimelineGrid
            day={day}
            rooms={rooms}
            bookings={bookings}
            onOpenBooking={(b) => navigate(appRoutes.hr.roomBookingDetail(b.id))}
            //  Bỏ trống khi thiếu quyền sửa = TẮT kéo thả. Không gác thì người
            //  chỉ được xem vẫn kéo được khối, thấy nó nhảy sang chỗ mới, rồi ăn
            //  403 và khối bật về — họ sẽ tưởng hệ thống lỗi chứ không nghĩ là
            //  mình không có quyền.
            onReschedule={
              can('room_booking', 'write')
                ? (booking, roomId, start, end) =>
                    reschedule.mutate({ id: booking.id, roomId, start, end })
                : undefined
            }
            onPickSlot={(roomId, hour) =>
              //  Mang sẵn phòng + giờ sang form đặt: người dùng vừa nhìn thấy
              //  chỗ trống, bắt họ gõ lại đúng con số đó là thao tác thừa.
              //
              //  ⚠️ Giờ là số THẬP PHÂN (`9.5` = 9:30) từ khi ô bấm chia nửa
              //  tiếng — ghép thẳng vào chuỗi thì ra `9.5:00`, một giờ không tồn
              //  tại và ô `datetime-local` bỏ trống trơn.
              navigate(
                `${appRoutes.hr.roomBookingNew}?room_id=${roomId}` +
                  `&start=${dateParam}T${formatSlotHour(hour)}`,
              )
            }
          />
        )}
      </Card>
    </PageContainer>
  )
}
