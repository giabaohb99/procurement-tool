import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Search } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appConfig } from '@/core/config/app-config'
import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import type { ListParams } from '@/shared/types/api'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
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

  return (
    <PageContainer fill>
      <PageHeader
        title="Phiếu đặt phòng họp"
        description="Đặt phòng, theo dõi phiếu và duyệt phiếu của người khác."
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

      <Tabs
        value={tab || TAB_MINE}
        onValueChange={setTab}
        className="flex min-h-0 flex-1 flex-col"
      >
        <TabsList>
          <TabsTrigger value={TAB_TO_APPROVE}>
            Cần tôi duyệt
            {/*  Con số chỉ hiện khi KHÁC 0: một huy hiệu «0» cạnh nhãn đọc ra
                 như cảnh báo, mà nó đang nói "không có gì cả". */}
            {waiting > 0 && (
              <Badge className="ml-1.5 border-sky-300 bg-sky-100 text-sky-800 dark:border-sky-700 dark:bg-sky-950 dark:text-sky-200">
                {waiting}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value={TAB_MINE}>Phiếu của tôi</TabsTrigger>
          <TabsTrigger value={TAB_HANDLED}>Tôi đã duyệt</TabsTrigger>
        </TabsList>

        {/*  Mỗi tab một `Card` riêng chứ không bọc chung ngoài `Tabs`: bảng chạy
             `fillHeight` nên nó cần đúng một khung cha có chiều cao xác định.
             `min-w-0` là bắt buộc — thiếu nó thì thẻ phình ra ngoài và CẢ TRANG
             trượt ngang (lỗi vá ngày 04/09/2026 ở màn Đơn nghỉ phép). */}
        <TabsContent value={TAB_TO_APPROVE} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-4">
            <RoomInboxTab mode="to-approve" />
          </Card>
        </TabsContent>

        <TabsContent value={TAB_MINE} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-4">
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
              storageKey="hr.room-bookings"
              onRowClick={(b) => navigate(appRoutes.hr.roomBookingDetail(b.id))}
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
                  <div className="relative min-w-56 flex-1 md:max-w-xs">
                    <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      className="pl-9"
                      placeholder="Tìm theo số phiếu hoặc nội dung…"
                      value={keyword}
                      onChange={(e) => setKeyword(e.target.value)}
                    />
                  </div>

                  <Select value={roomId} onValueChange={setRoomId}>
                    <SelectTrigger className="w-48" aria-label="Lọc theo phòng">
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

                  <Select value={status} onValueChange={setStatus}>
                    <SelectTrigger className="w-44" aria-label="Lọc theo trạng thái">
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
                </>
              }
            />
          </Card>
        </TabsContent>

        <TabsContent value={TAB_HANDLED} className="mt-3 flex min-h-0 flex-1">
          <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-4">
            <RoomInboxTab mode="handled" />
          </Card>
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
