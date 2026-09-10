import { useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useScrolled } from '@/shared/hooks/use-scrolled'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { QuickFilterField, QuickFilterSheet } from '@/shared/ui/quick-filter-sheet'
import { SearchField } from '@/shared/ui/search-field'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
import { RoomBookingCard } from '../components/room-booking-card'
import {
  codeColumn,
  requesterColumn,
  roomColumn,
  statusColumn,
  timeColumns,
  titleColumn,
} from '../components/room-booking-columns'
import { RoomInboxTab } from '../components/room-inbox-tab'
import { RoomSectionTabs } from '../components/room-section-tabs'
import { useMeetingRooms, useRoomBookings, useRoomToApprove } from '../hooks/use-room'
import { ROOM_BOOKING_STATUS, ROOM_BOOKING_STATUS_LABELS, type RoomBooking } from '../types/room'

import { LIST_TABS_STICKY, LIST_TOOLBAR_STICKY } from '../utils/list-sticky'
import { TAB_LIST_UNDERLINE, TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'

const ALL = 'all'
const TAB_TO_APPROVE = 'to-approve'
const TAB_MINE = 'mine'
const TAB_HANDLED = 'handled'

/**
 * PHIẾU ĐẶT PHÒNG — ba tab, cùng khuôn với màn Đơn nghỉ phép (CR-260):
 * **Cần tôi duyệt · Phiếu của tôi · Tôi đã duyệt**.
 *
 * Ba tab chứ không một danh sách phẳng vì ba câu hỏi khác nhau và của những
 * người khác nhau: *có việc gì chờ tôi ký không* · *phiếu tôi đặt tới đâu rồi* ·
 * *hôm qua tôi ký cái gì*. Trộn vào một bảng thì việc cần ký (thường 1-2 dòng)
 * chìm giữa hàng trăm dòng cũ.
 *
 * Tab «Cần tôi duyệt» đứng ĐẦU và mang huy hiệu số: đó là thứ có hạn, hai tab
 * kia thì không.
 */
export function RoomBookingListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()

  const [tab, setTab] = useUrlParamState('tab', TAB_MINE)
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam()
  const [status, setStatus] = useUrlParamState('status', ALL)
  const [roomId, setRoomId] = useUrlParamState('room_id', ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)

  const { data: roomData } = useMeetingRooms()
  //  Con số trên tab lấy từ chính hàng đợi của tab đó — không đếm ước lượng ở
  //  chỗ khác rồi lệch với danh sách bên trong.
  const { data: inbox } = useRoomToApprove()
  const waiting = inbox?.items.length ?? 0

  //  Dải ghim đầu trang đổ bóng khi có nội dung trôi bên dưới — xem
  //  `list-sticky.ts`. Đo ở `Tabs` vì nó nằm cùng khung cuộn với hai dải.
  const tabsRef = useRef<HTMLDivElement>(null)
  const scrolled = useScrolled(tabsRef)

  const params = useMemo<ListParams>(() => {
    const p: ListParams = { page, page_size: pageSize }
    if (debouncedValue) p.search = debouncedValue
    if (status !== ALL) p.status = status
    if (roomId !== ALL) p.room_id = roomId
    return p
  }, [page, pageSize, debouncedValue, status, roomId])

  const { data, isLoading, isError } = useRoomBookings(params, tab === TAB_MINE)

  const columns = useMemo<DataTableColumn<RoomBooking>[]>(
    () => [
      codeColumn<RoomBooking>(),
      statusColumn<RoomBooking>(),
      titleColumn<RoomBooking>(),
      roomColumn<RoomBooking>(),
      ...timeColumns<RoomBooking>(),
      requesterColumn<RoomBooking>(),
      {
        key: 'attendee_count',
        header: 'Số người',
        width: 100,
        align: 'right',
        cell: (b) =>
          b.attendee_count ? (
            <span className="tabular-nums">{b.attendee_count}</span>
          ) : (
            <span className="text-muted-foreground/50">—</span>
          ),
      },
    ],
    [],
  )

  const isFiltering = Boolean(debouncedValue) || status !== ALL || roomId !== ALL

  //  Hai ô chọn dựng MỘT lần rồi đặt vào hai chỗ (hàng ngang ở màn rộng · tờ
  //  trượt ở màn hẹp); state nằm trên URL nên hai bản luôn nói cùng giá trị.
  const roomSelect = (
    <Select value={roomId} onValueChange={setRoomId}>
      <SelectTrigger className="w-full md:w-48" aria-label="Lọc theo phòng">
        <SelectValue placeholder="Phòng" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Tất cả phòng</SelectItem>
        {(roomData?.items ?? []).map((room) => (
          <SelectItem key={room.id} value={String(room.id)}>
            {room.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  const statusSelect = (
    <Select value={status} onValueChange={setStatus}>
      <SelectTrigger className="w-full md:w-44" aria-label="Lọc theo trạng thái">
        <SelectValue placeholder="Trạng thái" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>Mọi trạng thái</SelectItem>
        {Object.values(ROOM_BOOKING_STATUS).map((value) => (
          <SelectItem key={value} value={String(value)}>
            {ROOM_BOOKING_STATUS_LABELS[value]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  //  ⚠️ `fill` (trang cao bằng khung, phần cuộn nằm BÊN TRONG) chỉ bật từ `md`
  //  trở lên — `max-md:h-auto` gỡ `h-full` mà `fill` đặt. Cùng lý do đã ghi ở
  //  `leave-request-list-page`: trên máy 390px, sau tiêu đề · nút · hai hàng
  //  tab · thanh lọc thì ô cuộn bên trong chỉ còn ~300px, và đó là cuộn LỒNG —
  //  vuốt trúng phần ngoài khe thì trang không nhúc nhích, người dùng đọc ra là
  //  màn hình đơ.
  return (
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Phiếu đặt phòng họp"
        //  ⚠️ Dòng mô tả ẨN trên máy hẹp: là câu giới thiệu, đọc một lần rồi
        //  thôi, nhưng chiếm hai dòng (~40px) ở đầu MỌI lần mở màn.
        description={
          <span className="max-md:hidden">
            Đặt phòng, theo dõi phiếu và duyệt phiếu của người khác.
          </span>
        }
        actions={
          can('room_booking', 'create') ? (
            //  `w-full` chỉ ăn nhờ nhóm nút của `PageHeader` cũng `max-md:w-full`.
            <Button
              className="w-full md:w-auto"
              onClick={() => navigate(appRoutes.hr.roomBookingNew)}
            >
              <Plus className="size-4" />
              Đặt phòng
            </Button>
          ) : undefined
        }
      />

      <RoomSectionTabs />

      {/*  `group` + `data-scrolled` là đường dẫn tín hiệu «trang đã cuộn» xuống
           tới dải ghim nằm sâu bên trong (thanh công cụ do `DataTable` vẽ, tầng
           trang không với tới được bằng prop) — xem `list-sticky.ts`. */}
      <Tabs
        ref={tabsRef}
        value={tab || TAB_MINE}
        onValueChange={setTab}
        data-scrolled={scrolled ? '' : undefined}
        className="group flex min-h-0 flex-1 flex-col"
      >
        {/*  Màn hẹp: dải tab trải hết hàng, chia đều ba phần, GHIM đỉnh trang
             khi cuộn, và đổi sang kiểu GẠCH CHÂN để không lẫn với hàng chuyển
             màn ngay phía trên — xem `shared/ui/tab-underline.ts`. `TabsList` mặc
             định `w-fit` nên trên điện thoại ba tab bó vào mép trái, chừa một
             khoảng trống vô nghĩa bên phải, mà đây là chỗ chuyển qua lại nhiều
             nhất của cả màn. */}
        <div className={LIST_TABS_STICKY}>
        <TabsList className={cn('w-full shrink-0 md:w-fit', TAB_LIST_UNDERLINE)}>
          <TabsTrigger
            value={TAB_TO_APPROVE}
            className={cn('min-w-0 px-2 text-xs md:px-3 md:text-sm', TAB_TRIGGER_UNDERLINE)}
          >
            Cần tôi duyệt
            {/*  Con số chỉ hiện khi KHÁC 0: một huy hiệu «0» cạnh nhãn đọc ra
                 như cảnh báo, mà nó đang nói "không có gì cả". */}
            {waiting > 0 && (
              <Badge className="ml-1.5 border-sky-300 bg-sky-100 text-sky-800 dark:border-sky-700 dark:bg-sky-950 dark:text-sky-200">
                {waiting}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger
            value={TAB_MINE}
            className={cn('min-w-0 px-2 text-xs md:px-3 md:text-sm', TAB_TRIGGER_UNDERLINE)}
          >
            Phiếu của tôi
          </TabsTrigger>
          <TabsTrigger
            value={TAB_HANDLED}
            className={cn('min-w-0 px-2 text-xs md:px-3 md:text-sm', TAB_TRIGGER_UNDERLINE)}
          >
            Tôi đã duyệt
          </TabsTrigger>
        </TabsList>
        </div>

        {/*  Mỗi tab một `Card` riêng chứ không bọc chung ngoài `Tabs`: bảng chạy
             `fillHeight` nên nó cần đúng một khung cha có chiều cao xác định.
             `min-w-0` là bắt buộc — thiếu nó thì thẻ phình ra ngoài và CẢ TRANG
             trượt ngang (lỗi vá ngày 04/09/2026 ở màn Đơn nghỉ phép). */}
        <TabsContent value={TAB_TO_APPROVE} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
            <RoomInboxTab mode="to-approve" />
          </Card>
        </TabsContent>

        <TabsContent value={TAB_MINE} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
            <DataTable
              fillHeight
              columns={columns}
              rows={data?.items}
              getRowId={(b) => b.id}
              isLoading={isLoading}
              isError={isError}
              emptyMessage={
                isFiltering
                  ? 'Không có phiếu nào khớp bộ lọc.'
                  : 'Chưa có phiếu đặt phòng nào. Bấm «Đặt phòng» để tạo.'
              }
              toolbarClassName={LIST_TOOLBAR_STICKY}
              storageKey="hr.room-bookings"
              onRowClick={(b) => navigate(appRoutes.hr.roomBookingDetail(b.id))}
              //  Màn hẹp: thẻ thay bảng. Giữ huy hiệu trạng thái — đây là câu
              //  hỏi đầu tiên của người đặt («phiếu của tôi tới đâu rồi»).
              mobileCard={(b) => <RoomBookingCard booking={b} />}
              pagination={{
                page,
                pageSize,
                total: data?.total ?? 0,
                onPageChange: setPage,
                onPageSizeChange: setPageSize,
                unitLabel: 'phiếu',
              }}
              toolbar={
                <>
                  {/*  Khổ hẹp: ô tìm chiếm trọn hàng, hai ô chọn dọn vào tờ
                       trượt — ba thứ này xếp ngang cần ~700px, mà thanh công cụ
                       lại đang GHIM đầu trang nên mỗi hàng thừa là một hàng che
                       mất danh sách suốt cả buổi. */}
                  {/*  Câu gợi ý phải ĐỌC HẾT được ở khổ hẹp: ô này chỉ còn
                       142px sau khi chia chỗ cho nút Bộ lọc và nút Tải lại, mà
                       «Tìm theo số phiếu hoặc nội dung…» cần 222px — nó cụt
                       giữa chừng thành «Tìm theo số phiếu hoặ». Một ô tìm không
                       nói nổi mình tìm được những gì thì người dùng đoán, và
                       thường đoán là chỉ tìm được mã. 139px, vừa khít. */}
                  <SearchField
                    value={keyword}
                    onChange={setKeyword}
                    placeholder="Tìm phiếu, nội dung…"
                    className="md:min-w-56 md:max-w-xs"
                  />

                  <QuickFilterSheet
                    activeCount={(roomId !== ALL ? 1 : 0) + (status !== ALL ? 1 : 0)}
                    onClearAll={() => {
                      setRoomId(ALL)
                      setStatus(ALL)
                    }}
                  >
                    <QuickFilterField label="Phòng">{roomSelect}</QuickFilterField>
                    <QuickFilterField label="Trạng thái">{statusSelect}</QuickFilterField>
                  </QuickFilterSheet>

                  <div className="hidden items-center gap-3 md:flex md:flex-wrap">
                    {roomSelect}
                    {statusSelect}
                  </div>
                </>
              }
            />
          </Card>
        </TabsContent>

        <TabsContent value={TAB_HANDLED} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
            <RoomInboxTab mode="handled" />
          </Card>
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
