import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useRoomHandled, useRoomToApprove } from '../hooks/use-room'
import type { RoomInboxRow } from '../types/room'
import {
  codeColumn,
  flowColumn,
  myTaskColumns,
  requesterColumn,
  roomColumn,
  statusColumn,
  timeColumns,
  titleColumn,
} from './room-booking-columns'

/**
 * Hai tab HỘP VIỆC DUYỆT — «Cần tôi duyệt» và «Tôi đã duyệt».
 *
 * Một component cho cả hai vì chúng chỉ khác nhau ở nguồn dữ liệu và vài cột;
 * tách đôi là hai bản chép cùng một bảng.
 *
 * ⚠️ Tab «Tôi đã duyệt» KHÔNG dựng cột «Việc của tôi» và «Hạn xử lý»: mọi dòng
 * ở đó đều do chính người đang xem quyết, nên hai cột ấy chỉ lặp lại tên tab và
 * một mốc giờ không dùng để làm gì — trong khi chúng chiếm 330px đầu bảng, đẩy
 * những cột thật sự phân biệt các dòng trôi sang phải (bài học của Nghỉ phép).
 */
export function RoomInboxTab({ mode }: { mode: 'to-approve' | 'handled' }) {
  const navigate = useNavigate()
  const toApprove = useRoomToApprove(mode === 'to-approve')
  const handled = useRoomHandled(30, mode === 'handled')
  const query = mode === 'to-approve' ? toApprove : handled

  const columns = useMemo<DataTableColumn<RoomInboxRow>[]>(
    () => [
      codeColumn<RoomInboxRow>(),
      statusColumn<RoomInboxRow>(),
      titleColumn<RoomInboxRow>(),
      roomColumn<RoomInboxRow>(),
      ...timeColumns<RoomInboxRow>(),
      requesterColumn<RoomInboxRow>(),
      flowColumn(),
      ...(mode === 'to-approve' ? myTaskColumns() : []),
    ],
    [mode],
  )

  return (
    <DataTable
      fillHeight
      columns={columns}
      rows={query.data?.items}
      getRowId={(r) => r.id}
      isLoading={query.isLoading}
      isError={query.isError}
      emptyMessage={
        mode === 'to-approve'
          ? 'Không có phiếu nào đang chờ bạn duyệt.'
          : 'Bạn chưa duyệt phiếu đặt phòng nào trong 30 ngày qua.'
      }
      storageKey={`hr.room-${mode}`}
      onRowClick={(r) => navigate(appRoutes.hr.roomBookingDetail(r.id))}
    />
  )
}
