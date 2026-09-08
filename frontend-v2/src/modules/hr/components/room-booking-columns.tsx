import type { DataTableColumn } from '@/shared/data-table'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import type { RoomBooking, RoomInboxRow } from '../types/room'
import { formatTimeRange } from '../utils/room-time'
import { RoomStatusBadge } from './room-status-badge'

/**
 * Cột dùng chung cho BA tab của màn Phiếu đặt phòng.
 *
 * Khai ở một chỗ vì ba tab hỏi cùng một câu — *phiếu nào, phòng nào, giờ nào* —
 * chỉ khác ở vài cột riêng (hạn xử lý ở tab chờ ký, thời điểm ký ở tab đã ký).
 * Chép ba bản thì sớm muộn ba bảng lệch nhau về thứ tự và bề rộng cột.
 */

export function codeColumn<T extends RoomBooking>(): DataTableColumn<T> {
  return {
    key: 'code',
    header: 'Số phiếu',
    width: 110,
    hideable: false,
    defaultPinned: true,
    cell: (b) => <span className="font-semibold text-primary">{b.code}</span>,
  }
}

export function statusColumn<T extends RoomBooking>(): DataTableColumn<T> {
  return {
    key: 'status',
    header: 'Trạng thái',
    width: 140,
    cell: (b) => <RoomStatusBadge status={b.status} label={b.status_label} />,
  }
}

export function titleColumn<T extends RoomBooking>(): DataTableColumn<T> {
  return {
    key: 'title',
    header: 'Nội dung cuộc họp',
    width: 240,
    wrap: true,
    minWidth: 180,
    cell: (b) => <span className="font-medium">{b.title}</span>,
  }
}

export function roomColumn<T extends RoomBooking>(): DataTableColumn<T> {
  return {
    key: 'room_name',
    header: 'Phòng',
    width: 170,
    cell: (b) => b.room_name || `#${b.room_id}`,
  }
}

/** Ngày + khung giờ — hai cột luôn đi cùng nhau. */
export function timeColumns<T extends RoomBooking>(): DataTableColumn<T>[] {
  return [
    {
      key: 'start_at',
      header: 'Ngày họp',
      width: 120,
      sortable: true,
      cell: (b) => formatDate(b.start_at),
    },
    {
      key: 'time',
      header: 'Khung giờ',
      width: 140,
      //  Hai đầu giờ đứng CẠNH NHAU trong một ô: tách hai cột thì mắt phải nhảy
      //  qua lại để đọc một khoảng thời gian duy nhất.
      cell: (b) => (
        <span className="tabular-nums">{formatTimeRange(b.start_at, b.end_at)}</span>
      ),
    },
  ]
}

export function requesterColumn<T extends RoomBooking>(): DataTableColumn<T> {
  return {
    key: 'requester_name',
    header: 'Người đặt',
    width: 170,
    cell: (b) => b.requester_name || '—',
  }
}

/**
 * Luồng duyệt — CHỮ một dòng do backend dựng (`steps_service._summary`).
 *
 * ⚠️ Không vẽ dải chấm: bản đó đã dựng rồi bỏ ở Nghỉ phép ngày 03/09/2026 —
 * trong ô bảng cao 35px nó đọc ra như một dãy biểu tượng lỗi.
 */
export function flowColumn(): DataTableColumn<RoomInboxRow> {
  return {
    key: 'flow',
    header: 'Luồng duyệt',
    width: 200,
    cell: (row) =>
      row.flow?.text ? (
        <span className="text-muted-foreground">{row.flow.text}</span>
      ) : (
        <span className="text-muted-foreground/50">—</span>
      ),
  }
}

/** Việc của tôi trên phiếu + hạn xử lý — chỉ có nghĩa ở tab «Cần tôi duyệt». */
export function myTaskColumns(): DataTableColumn<RoomInboxRow>[] {
  return [
    {
      key: 'my_task',
      header: 'Việc của tôi',
      width: 180,
      cell: (row) => row.task?.node_name || 'Chờ tôi duyệt',
    },
    {
      key: 'due_at',
      header: 'Hạn xử lý',
      width: 150,
      cell: (row) =>
        row.task?.due_at ? (
          <span className="tabular-nums">{formatDateTime(row.task.due_at)}</span>
        ) : (
          <span className="text-muted-foreground/50">—</span>
        ),
    },
  ]
}
