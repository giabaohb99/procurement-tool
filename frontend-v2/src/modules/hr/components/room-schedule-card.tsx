import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { formatDate } from '@/shared/utils/format-date'
import { useRoomBookings } from '../hooks/use-room'
import { BLOCKING_ROOM_STATUSES, type RoomBooking } from '../types/room'
import { formatTimeRange, toApiTime, toLocalInput } from '../utils/room-time'
import { RoomStatusBadge } from './room-status-badge'

/**
 * LỊCH ĐẶT CỦA MỘT PHÒNG — tab trong trang chi tiết phòng.
 *
 * Danh mục phòng mà chỉ khai được tên và sức chứa thì mới là *danh mục*; thứ
 * khiến nó thành **quản lý phòng** là trả lời được hai câu ngay tại chỗ: *"phòng
 * này sắp tới ai giữ"* và *"nó có thật sự được dùng không"*. Câu sau quyết định
 * việc dẹp bớt hay đầu tư thêm phòng, mà không có bảng này thì phải đi đếm tay
 * ở màn Lịch từng ngày một.
 *
 * ⚠️ Tách **Sắp tới / Đã qua** chứ không đổ chung một bảng xếp theo ngày: hai
 * câu hỏi khác nhau — cái đầu để xếp lịch, cái sau để nhìn lại. Trộn vào nhau
 * thì phần sắp tới (thường 2-3 dòng) chìm giữa hàng trăm dòng cũ.
 */
export function RoomScheduleCard({ roomId }: { roomId: number }) {
  const navigate = useNavigate()
  const [tab, setTab] = useState('upcoming')

  //  Mốc "bây giờ" chốt MỘT LẦN lúc dựng: tính lại mỗi render thì khóa query đổi
  //  liên tục và bảng tự gọi lại API không lý do.
  const now = useMemo(() => toApiTime(toLocalInput(new Date())), [])

  const upcoming = useRoomBookings(
    { page: 1, page_size: 50, room_id: roomId, from_time: now, sort_by: 'start_at', sort_dir: 'asc' },
    roomId > 0,
  )
  const past = useRoomBookings(
    { page: 1, page_size: 50, room_id: roomId, to_time: now, sort_by: 'start_at', sort_dir: 'desc' },
    roomId > 0,
  )

  const columns = useMemo<DataTableColumn<RoomBooking>[]>(
    () => [
      {
        key: 'start_at',
        header: 'Ngày',
        width: 120,
        cell: (b) => formatDate(b.start_at),
      },
      {
        key: 'time',
        header: 'Khung giờ',
        width: 140,
        cell: (b) => (
          <span className="tabular-nums">{formatTimeRange(b.start_at, b.end_at)}</span>
        ),
      },
      {
        key: 'title',
        header: 'Nội dung',
        width: 260,
        wrap: true,
        minWidth: 180,
        cell: (b) => <span className="font-medium">{b.title}</span>,
      },
      {
        key: 'requester_name',
        header: 'Người đặt',
        width: 180,
        cell: (b) => b.requester_name || '—',
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 150,
        cell: (b) => <RoomStatusBadge status={b.status} label={b.status_label} />,
      },
      {
        key: 'code',
        header: 'Số phiếu',
        width: 110,
        cell: (b) => <span className="text-muted-foreground">{b.code}</span>,
      },
    ],
    [],
  )

  //  Phiếu ĐÃ HỦY / bị từ chối vẫn nằm trong bảng «Đã qua» — chúng là lịch sử
  //  thật của phòng. Nhưng ở «Sắp tới» thì bỏ: phòng không bị giữ, hiện ra chỉ
  //  làm người xếp lịch tưởng nó đã kín.
  const upcomingRows = (upcoming.data?.items ?? []).filter((b) =>
    BLOCKING_ROOM_STATUSES.includes(b.status),
  )

  return (
    <Tabs value={tab} onValueChange={setTab} className="space-y-3">
      <TabsList>
        <TabsTrigger value="upcoming">Sắp tới ({upcomingRows.length})</TabsTrigger>
        <TabsTrigger value="past">Đã qua</TabsTrigger>
      </TabsList>

      <TabsContent value="upcoming">
        <DataTable
          columns={columns}
          rows={upcomingRows}
          getRowId={(b) => b.id}
          isLoading={upcoming.isLoading}
          isError={upcoming.isError}
          emptyMessage="Phòng này chưa có ai giữ trong thời gian tới."
          storageKey="hr.room-schedule-upcoming"
          onRowClick={(b) => navigate(appRoutes.hr.roomBookingDetail(b.id))}
        />
      </TabsContent>

      <TabsContent value="past">
        <DataTable
          columns={columns}
          rows={past.data?.items}
          getRowId={(b) => b.id}
          isLoading={past.isLoading}
          isError={past.isError}
          emptyMessage="Phòng này chưa từng được đặt."
          storageKey="hr.room-schedule-past"
          onRowClick={(b) => navigate(appRoutes.hr.roomBookingDetail(b.id))}
        />
      </TabsContent>
    </Tabs>
  )
}
