import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronDown, ChevronLeft, ChevronRight, Plus } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { Calendar } from '@/shared/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { SearchField } from '@/shared/ui/search-field'
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

  //  Hai bản nhãn ngày, dựng sẵn để phần JSX chỉ còn việc chọn — xem chỗ dùng.
  const dateOnly = { day: '2-digit', month: '2-digit', year: 'numeric' } as const
  const fullDayLabel = day.toLocaleDateString('vi-VN', { weekday: 'long', ...dateOnly })
  //  ⚠️ `weekday: 'narrow'`, KHÔNG phải `'short'`: với `vi-VN` thì `'short'` ra
  //  «Thứ 4, 09/09/2026» — dài gần bằng bản đầy đủ và vẫn bị cắt trên màn 390px.
  //  `'narrow'` mới ra «T4», thứ thật sự vừa chỗ.
  const shortDayLabel = day.toLocaleDateString('vi-VN', { weekday: 'narrow', ...dateOnly })

  return (
    <PageContainer fill>
      <PageHeader
        title="Lịch đặt phòng"
        description="Phòng nào đang bận, ai giữ, tới mấy giờ. Bấm vào ô trống để đặt ngay."
        actions={
          can('room_booking', 'create') ? (
            //  Nhóm nút của `PageHeader` chiếm trọn hàng ở khổ hẹp, nên một nút
            //  co theo chữ nép ở mép phải trông như bị bỏ quên giữa hàng trống.
            <Button
              className="max-md:w-full"
              onClick={() => navigate(appRoutes.hr.roomBookingNew)}
            >
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
          {/*  ⚠️ CHÚ GIẢI MÀU bỏ hẳn dưới `md`. Ở khổ hẹp lưới đổi thành danh
               sách (`RoomDayList`) và mỗi phiếu ở đó tự mang huy hiệu chữ, nên
               ba mục chú giải chỉ còn là một hàng đi giải nghĩa thứ ngay bên
               dưới đã nói thành lời — mà «Ngoài giờ làm» thì hết nghĩa luôn,
               danh sách không có dải nền giờ nào để tô. */}
          <div className="flex h-8 items-center gap-3 border-r pr-3 text-xs text-muted-foreground max-md:hidden">
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

          {/*  ⚠️ Ở khổ hẹp cụm này chiếm TRỌN bề ngang và chia thành đúng HAI
               hàng — *ngày + điều hướng*, rồi *lọc + con số*. Bản trước để nguyên
               `ml-auto` với bốn phần tử co theo nội dung, nên trên máy 390px nó
               rơi thành **bốn hàng chồng nhau, ~200px** trước khi thấy dòng dữ
               liệu đầu tiên (khách báo 09/09/2026).

               ⚠️ Chia hàng bằng HAI KHỐI BỌC tường minh, không trông vào
               `flex-wrap`: bốn phần tử cùng `flex-wrap` thì hai ô co giãn (nút
               ngày và ô lọc) tranh nhau chỗ, và bản thử đầu cho ra nút ngày bị
               bóp còn *«Thứ …»* trong khi ô lọc trèo lên cùng hàng. `md:contents`
               gỡ hai khối bọc ở khổ rộng để bốn phần tử về lại đúng một hàng
               ngang như cũ; `md:order-*` giữ nguyên thứ tự trái→phải của bản
               desktop (con số · lọc · ngày · điều hướng). */}
          <div className="flex w-full flex-col gap-2 md:ml-auto md:w-auto md:flex-row md:flex-wrap md:items-center">
            <div className="flex items-center gap-2 md:contents">

            {/*  TÊN NGÀY là nút mở lịch — gộp hai thứ vốn lặp nhau: bản đầu có
                 cả dòng «Thứ Sáu, 04/09/2026» LẪN một ô `<input type="date">`
                 ghi đúng ngày đó ngay bên cạnh. Ô ngày gốc của trình duyệt còn
                 mỗi hệ điều hành một kiểu và trên Windows hiện `mm/dd/yyyy`
                 trong khi cả hệ dùng `dd/mm/yyyy` — xem `shared/ui/date-picker.tsx`. */}
            <Popover open={openCalendar} onOpenChange={setOpenCalendar}>
              <PopoverTrigger asChild>
                <Button
                  variant="ghost"
                  className="h-8 min-w-0 flex-1 justify-start gap-1.5 px-2 font-semibold md:order-3 md:flex-none md:text-base"
                  aria-label="Chọn ngày xem lịch"
                >
                  {/*  Khổ hẹp rút «Thứ Tư» thành «T4» và bỏ cỡ chữ `text-base`:
                       cả cụm ngày + ba nút điều hướng phải nằm trọn MỘT hàng
                       358px, bản đầy đủ một mình đã ăn ~190px. */}
                  <span className="truncate md:hidden">{shortDayLabel}</span>
                  <span className="truncate max-md:hidden">{fullDayLabel}</span>
                  <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
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
            <div className="flex h-8 shrink-0 items-center rounded-md border md:order-4">
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

            <div className="flex items-center gap-2 md:contents">
              {/*  ⚠️ Con số tổng ẨN dưới `md`. Ở khổ hẹp nó ngồi cùng hàng với
                   ô lọc và bóp ô đó còn ~205px, đủ để câu gợi ý bị cắt giữa
                   chừng («Lọc phòng, tầng, thi») — một ô tìm mà không đọc nổi
                   nó tìm được những gì (khách báo 09/09/2026). Bỏ đi không mất
                   thông tin: hai tiêu đề phần ngay dưới đã nói *«Đang có lịch ·
                   N phòng»* và *«Còn trống · M phòng»*. Chỉ «lượt giữ» là không
                   còn, mà con số ấy chính là mấy dòng phiếu đang bày bên dưới. */}
              <span className="flex h-8 shrink-0 items-center rounded-md bg-muted px-2.5 text-xs text-muted-foreground tabular-nums max-md:hidden md:order-1">
                {heldCount} lượt giữ ·{' '}
                {rooms.length === allRooms.length
                  ? `${allRooms.length} phòng`
                  : `${rooms.length}/${allRooms.length} phòng`}
              </span>

              {/*  Chỉ dựng ô lọc khi danh sách đủ dài để phải lọc — công ty bốn
                   phòng mà bày thêm một ô tìm là thêm thứ để đọc mà không dùng tới.

                   Dùng `SearchField` chứ không `<Input>` trần: nó mang sẵn **nút
                   xóa chữ**, thứ đáng giá nhất trên điện thoại — không có thì bỏ
                   bộ lọc là giữ · kéo hai đầu · bấm xóa, cho một việc đáng ra một
                   chạm. `h-8` để giữ luật «mọi thứ trên thanh này cao đúng 32px»
                   ở khổ rộng. */}
              {allRooms.length > 6 && (
                <SearchField
                  className="h-8 md:order-2 md:w-52 md:flex-none"
                  placeholder="Lọc phòng, tầng, thiết bị…"
                  aria-label="Lọc phòng"
                  value={roomQuery}
                  onChange={setRoomQuery}
                />
              )}
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
