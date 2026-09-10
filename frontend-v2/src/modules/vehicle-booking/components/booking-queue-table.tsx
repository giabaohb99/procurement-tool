import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { BookingStatusBadge } from './status-pill'
import { BOOKING_STATUS_LABELS, type VehicleBooking } from '../types/vehicle-booking'

const ALL = 'all'

function formatDateTime(value: string): string {
  if (!value) return ''
  const [date, time] = value.split('T')
  if (!date) return value
  const [y, m, d] = date.split('-')
  const hm = (time ?? '').slice(0, 5)
  return `${d}/${m}/${y}${hm ? ` ${hm}` : ''}`
}

function fieldValue(row: VehicleBooking, key: string): string | number {
  if (key === 'status') return row.status
  if (key === 'start_time') return row.start_time || ''
  if (key === 'code') return row.code || ''
  if (key === 'purpose') return row.purpose || ''
  return ''
}

interface BookingQueueTableProps {
  rows: VehicleBooking[]
  emptyMessage?: string
  /** Ẩn ô lọc nhanh trạng thái (khi khối chỉ có một trạng thái, vd hàng chờ duyệt). */
  hideStatusFilter?: boolean
}

/**
 * Bảng gọn cho các khối "việc cần xử lý" trên trang Tổng quan Đặt xe: sắp xếp cột
 * + lọc nhanh trạng thái NGAY tại chỗ (client-side, danh sách đã giới hạn 8 dòng),
 * không kéo cả bộ lọc nâng cao của trang danh sách vào dashboard.
 */
export function BookingQueueTable({ rows, emptyMessage, hideStatusFilter }: BookingQueueTableProps) {
  const navigate = useNavigate()
  const [status, setStatus] = useState(ALL)
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const view = useMemo(() => {
    const filtered = status === ALL ? rows : rows.filter((r) => String(r.status) === status)
    if (!sortBy) return filtered
    const sorted = [...filtered].sort((a, b) => {
      const va = fieldValue(a, sortBy)
      const vb = fieldValue(b, sortBy)
      if (va < vb) return -1
      if (va > vb) return 1
      return 0
    })
    return sortDir === 'asc' ? sorted : sorted.reverse()
  }, [rows, status, sortBy, sortDir])

  const columns = useMemo<DataTableColumn<VehicleBooking>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã phiếu',
        width: 110,
        sortable: true,
        cell: (r) => <span className="font-medium tabular-nums">{r.code}</span>,
      },
      { key: 'purpose', header: 'Mục đích', minWidth: 160, sortable: true, wrap: true, cell: (r) => r.purpose },
      {
        key: 'route',
        header: 'Lộ trình',
        minWidth: 160,
        wrap: true,
        cell: (r) => [r.start_location, r.end_location].filter(Boolean).join(' → ') || '—',
      },
      {
        key: 'start_time',
        header: 'Thời gian đi',
        width: 140,
        sortable: true,
        cell: (r) => <span className="tabular-nums">{formatDateTime(r.start_time)}</span>,
      },
      {
        key: 'status',
        header: 'Trạng thái',
        width: 130,
        sortable: true,
        cell: (r) => <BookingStatusBadge status={r.status} driverStatus={r.driver_status} />,
      },
    ],
    [],
  )

  return (
    <div className="flex flex-col gap-3">
      {!hideStatusFilter && (
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="h-8 w-44 text-xs">
            <SelectValue placeholder="Lọc trạng thái" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Mọi trạng thái</SelectItem>
            {Object.entries(BOOKING_STATUS_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
      <DataTable
        columns={columns}
        rows={view}
        getRowId={(r) => r.id}
        onRowClick={(r) => navigate(appRoutes.vehicleBooking.detail(r.id))}
        emptyMessage={emptyMessage ?? 'Không có phiếu nào.'}
        sortBy={sortBy}
        sortDir={sortDir}
        onSortChange={(by, dir) => {
          setSortBy(by)
          setSortDir(dir)
        }}
      />
    </div>
  )
}
